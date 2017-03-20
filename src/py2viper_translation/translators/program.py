import ast

from collections import OrderedDict
from py2viper_translation.lib.constants import (
    ERROR_NAME,
    PRIMITIVES,
    RESULT_NAME
)
from py2viper_translation.lib.program_nodes import (
    MethodType,
    PythonClass,
    PythonField,
    PythonMethod,
    PythonModule,
    PythonType,
    PythonVar,
)
from py2viper_translation.lib.typedefs import (
    Domain,
    Expr,
    Field,
    Function,
    Method,
    Predicate,
    Program,
    Stmt,
    StmtsAndExpr,
)
from py2viper_translation.lib.util import (
    InvalidProgramException,
    UnsupportedException,
)
from py2viper_translation.translators.abstract import Context
from py2viper_translation.translators.common import CommonTranslator
from typing import List, Set, Tuple


class ProgramTranslator(CommonTranslator):
    def __init__(self, config: 'TranslatorConfig', jvm: 'JVM', source_file: str,
                 type_info: 'TypeInfo', viper_ast: 'ViperAST') -> None:
        super().__init__(config, jvm, source_file, type_info, viper_ast)
        self.required_names = {}

    def translate_field(self, field: PythonField,
                        ctx: Context) -> 'silver.ast.Field':
        return self.viper.Field(field.sil_name,
                                self.translate_type(field.type, ctx),
                                self.to_position(field.node, ctx),
                                self.no_info(ctx))

    def _translate_fields(self, cls: PythonClass,
                          ctx: Context) -> List['silver.ast.Field']:
        fields = []
        for field in cls.fields.values():
            if field.inherited is None:
                sil_field = self.translate_field(field, ctx)
                field.sil_field = sil_field
                fields.append(sil_field)

        return fields

    def create_global_var_function(self, var: PythonVar,
                                   ctx: Context) -> 'silver.ast.Function':
        """
        Creates a Viper function representing the given global variable.
        """
        type = self.translate_type(var.type, ctx)
        position = self.to_position(var.node, ctx)
        posts = []
        result = self.viper.Result(type, position, self.no_info(ctx))
        if var.type.name not in PRIMITIVES:
            posts.append(self.type_check(result, var.type, position, ctx))
        if hasattr(var, 'value'):
            stmt, value = self.translate_expr(var.value, ctx)
            if stmt:
                raise InvalidProgramException('purity.violated', var.node)
            body = value
            posts.append(self.viper.EqCmp(result, value, position,
                                          self.no_info(ctx)))
        else:
            body = None
        return self.viper.Function(var.sil_name, [], type, [], posts, body,
                                   self.to_position(var.node, ctx),
                                   self.no_info(ctx))

    def create_inherit_check(self, method: PythonMethod, cls: PythonClass,
                             ctx: Context) -> 'silver.ast.Callable':
        """
        Creates a Viper function/method with the contract of the overridden
        function which calls the overriding function, to check behavioural
        subtyping.
        """
        old_function = ctx.current_function
        ctx.current_function = method
        pos = self.viper.to_position(cls.node, ctx.position)
        ctx.position.append(('inheritance', pos))
        self.info = self.viper.SimpleInfo(['behavioural.subtyping'])

        self.bind_type_vars(method, ctx)

        params = []
        results = []
        args = []
        locals_before = set(method.locals.values())
        if method.type:
            results.append(method.result.decl)

        error_var = PythonVar(ERROR_NAME, None,
                              ctx.module.global_module.classes['Exception'])
        error_var.process(ERROR_NAME, self.translator)
        optional_error_var = error_var if method.declared_exceptions else None

        if method.declared_exceptions:
            results.append(error_var.decl)

        mname = ctx.module.get_fresh_name(cls.name + '_' + method.name +
                                          '_inherit_check')
        pres, posts = self.extract_contract(method, ERROR_NAME,
                                            False, ctx)
        if method.method_type == MethodType.normal:
            not_null = self.viper.NeCmp(next(iter(method.args.values())).ref(),
                                        self.viper.NullLit(self.no_position(ctx),
                                                           self.no_info(ctx)),
                                        self.no_position(ctx), self.no_info(ctx))
            new_type = self.type_factory.type_check(
                next(iter(method.args.values())).ref(), cls, pos, ctx,
                concrete=True)
            pres = [not_null, new_type] + pres

        for arg_name, arg in method.args.items():
            args.append(arg)
            params.append(arg.decl)

        stmts, end_lbl = self.inline_method(method, args, method.result,
                                            error_var, ctx)
        goto_end = self.viper.Goto(end_lbl.name(), self.no_position(ctx),
                                   self.no_info(ctx))
        stmts.append(goto_end)
        stmts += self.add_handlers_for_inlines(ctx)

        stmts.append(end_lbl)
        locals_after = set(method.locals.values())
        locals_diff = locals_after.symmetric_difference(locals_before)
        locals = [var.decl for var in locals_diff]
        result = self.create_method_node(
            ctx, mname, params, results, pres, posts, locals, stmts,
            self.no_position(ctx), self.no_info(ctx),
            method=method, overriding_check=True)

        ctx.current_function = old_function

        ctx.position.pop()
        self.info = None
        return result

    def create_override_check(self, method: PythonMethod,
                              ctx: Context) -> 'silver.ast.Callable':
        """
        Creates a Viper function/method with the contract of the overridden
        function which calls the overriding function, to check behavioural
        subtyping.
        """
        assert not method.pure
        old_function = ctx.current_function
        ctx.current_function = method.overrides
        pos = self.viper.to_position(method.node, ctx.position)
        ctx.position.append(('override', pos))
        self.info = self.viper.SimpleInfo(['behavioural.subtyping'])
        self._check_override_validity(method, ctx)

        self.bind_type_vars(method, ctx)

        params = []
        args = []

        mname = ctx.module.get_fresh_name(method.sil_name + '_override_check')
        pres, posts = self.extract_contract(method.overrides, '_err',
                                            False, ctx)
        self_arg = None
        has_subtype = None
        if method.cls and method.method_type == MethodType.normal:
            self_arg = method.overrides.args[next(iter(method.overrides.args))]
            not_null = self.viper.NeCmp(next(iter(method.args.values())).ref(),
                                        self.viper.NullLit(
                                            self.no_position(ctx),
                                            self.no_info(ctx)),
                                        self.no_position(ctx),
                                        self.no_info(ctx))
            pres = [not_null] + pres
            has_subtype = self.var_type_check(self_arg.sil_name, method.cls,
                                              pos,
                                              ctx, inhale_exhale=False)
        elif method.method_type == MethodType.class_method:
            cls_arg = next(iter(method.args.values())).ref()
            has_subtype = self.type_factory.subtype_check(cls_arg, method.cls,
                                                          pos, ctx)
        if method.name == '__init__':
            full_perm = self.viper.FullPerm(self.no_position(ctx),
                                            self.no_info(ctx))
            for cls in [method.cls, method.cls.superclass]:
                for name, field in cls.fields.items():
                    if field.inherited:
                        continue
                    field = self.viper.Field(field.sil_name,
                                             self.translate_type(field.type,
                                                                 ctx),
                                             self.no_position(ctx),
                                             self.no_info(ctx))
                    field_acc = self.viper.FieldAccess(self_arg.ref(), field,
                                                       self.no_position(ctx),
                                                       self.no_info(ctx))
                    acc = self.viper.FieldAccessPredicate(field_acc, full_perm,
                                                          self.no_position(ctx),
                                                          self.no_info(ctx))
                    pres.append(acc)

        for arg in method.overrides.args:
            params.append(method.overrides.args[arg].decl)
            args.append(method.overrides.args[arg].ref())

        called_name = method.sil_name
        ctx.position.pop()
        results, targets, body = self._create_override_check_body_impure(
            method, has_subtype, called_name, args, ctx)
        result = self.create_method_node(
            ctx, mname, params, results, pres, posts, [], body,
            self.no_position(ctx), self.no_info(ctx),
            method=method.overrides, overriding_check=True)

        ctx.current_function = old_function
        self.info = None
        return result

    def _create_override_check_body_impure(self, method: PythonMethod,
            has_subtype: Expr, calledname: str,
            args: List[Expr], ctx: Context) -> Tuple[List['ast.LocalVarDecl'],
                                                     List['ast.LocalVar'],
                                                     List[Stmt]]:
        results = []
        targets = []
        if method.type:
            type = self.translate_type(method.type, ctx)
            result_var_decl = self.viper.LocalVarDecl(RESULT_NAME, type,
                self.to_position(method.node, ctx), self.no_info(ctx))
            result_var_ref = self.viper.LocalVar(RESULT_NAME, type,
                self.to_position(method.node, ctx), self.no_info(ctx))
            results.append(result_var_decl)
            targets.append(result_var_ref)
        error_var_decl = self.viper.LocalVarDecl(ERROR_NAME, self.viper.Ref,
                                                 self.no_position(ctx),
                                                 self.no_info(ctx))
        error_var_ref = self.viper.LocalVar(ERROR_NAME, self.viper.Ref,
                                            self.no_position(ctx),
                                            self.no_info(ctx))
        if method.overrides.declared_exceptions:
            results.append(error_var_decl)
        if method.declared_exceptions:
            targets.append(error_var_ref)

        # Check that arg names match and default args are equal
        default_checks = []
        for (name1, arg1), (name2, arg2) in zip(method.args.items(),
                                                method.overrides.args.items()):
            error_string = ('"default value matches overridden method '
                            'for argument {0}"').format(name1)
            assert_pos = self.to_position(arg1.node, ctx, error_string)
            if name1 != name2:
                raise InvalidProgramException(arg1.node, 'invalid.override')
            if arg1.default or arg2.default:
                if not (arg1.default and arg2.default):
                    raise InvalidProgramException(arg1.node, 'invalid.override')
                val1 = arg1.default_expr
                val2 = arg2.default_expr
                eq = self.viper.EqCmp(val1, val2, assert_pos,
                                      self.no_info(ctx))
                assertion = self.viper.Assert(eq, assert_pos,
                                              self.no_info(ctx))
                default_checks.append(assertion)
        ctx.position.append(('overridden method',
                             self.viper.to_position(method.overrides.node,
                                                    ctx.position)))
        call = self.create_method_call_node(
            ctx, calledname, args, targets,
            self.to_position(method.node, ctx), self.no_info(ctx),
            target_method=method)
        ctx.position.pop()
        if has_subtype:
            subtype_assume = self.viper.Inhale(has_subtype,
                                               self.no_position(ctx),
                                               self.no_info(ctx))
            body = default_checks + [subtype_assume] + call
        else:
            body = default_checks + call
        return results, targets, body

    def _check_override_validity(self, method: PythonMethod,
                                 ctx: Context) -> None:
        """
        Checks if the given method overrides its equivalent in a superclass
        in a valid way, otherwise raises an InvalidProgramException.
        """
        if len(method.args) != len(method.overrides.args):
            raise InvalidProgramException(method.node, 'invalid.override')
        for exc_class in method.declared_exceptions:
            allowed = False
            for superexc in method.overrides.declared_exceptions:
                if exc_class.issubtype(superexc):
                    allowed = True
                    break
            if not allowed:
                raise InvalidProgramException(method.node, 'invalid.override')
                # TODO check if exceptional postconditions imply super postconds
        if method.pure:
            if not method.overrides.pure:
                raise InvalidProgramException(method.node, 'invalid.override')
        else:
            if method.overrides.pure:
                raise InvalidProgramException(method.node, 'invalid.override')

    def translate_default_args(self, method: PythonMethod,
                               ctx: Context) -> None:
        for arg in method.args.values():
            if arg.default:
                stmt, expr = self.translate_expr(arg.default, ctx)
                if stmt:
                    raise InvalidProgramException(arg.default,
                                                  'purity.violated')
                assert expr
                arg.default_expr = expr

    def _create_predefined_fields(self,
                                  ctx: Context) -> List[Field]:
        """
        Creates and returns fields needed for encoding various language
        features, e.g. collections, measures and iterators.
        """
        fields = []
        fields.append(self.viper.Field('__container', self.viper.Ref,
                                       self.no_position(ctx),
                                       self.no_info(ctx)))
        fields.append(self.viper.Field('__iter_index', self.viper.Int,
                                       self.no_position(ctx),
                                       self.no_info(ctx)))
        fields.append(self.viper.Field('__previous', self.viper.Ref,
                                       self.no_position(ctx),
                                       self.no_info(ctx)))
        fields.append(self.viper.Field('list_acc',
                                       self.viper.SeqType(self.viper.Ref),
                                       self.no_position(ctx),
                                       self.no_info(ctx)))
        fields.append(self.viper.Field('set_acc',
                                       self.viper.SetType(self.viper.Ref),
                                       self.no_position(ctx),
                                       self.no_info(ctx)))
        fields.append(self.viper.Field('dict_acc',
                                       self.viper.SetType(self.viper.Ref),
                                       self.no_position(ctx),
                                       self.no_info(ctx)))
        fields.append(self.viper.Field('Measure$acc',
                                       self.viper.SeqType(self.viper.Ref),
                                       self.no_position(ctx),
                                       self.no_info(ctx)))
        return fields

    def _add_all_used_names(self, initial: Set[str]) -> None:
        """
        Calculates the names of all methods and functions used by the program,
        based on the names reported to be used by the viper_ast module, and adds
        them to the given set.
        """
        used_names = initial
        to_add = list(self.viper.used_names)
        index = 0
        while index < len(to_add):
            current = to_add[index]
            if current not in used_names:
                used_names.add(current)
                if current in self.required_names:
                    to_add.extend(self.required_names[current])
            index = index + 1

    def _convert_silver_elements(self, sil_progs: List[Program],
                                 ctx: Context) -> Tuple[List[Domain],
                                                        List[Predicate],
                                                        List[Function],
                                                        List[Method]]:
        """
        Extracts domains, functions, predicates and methods from the given list
        of Silver programs, applies the necessary conversions (e.g. related to
        obligations) to them, and returns them in separate lists.
        """
        domains = []
        functions = []
        predicates = []
        methods = []

        used_names = set()
        self._add_all_used_names(used_names)

        # Reset used names set, we only need the additional ones used by the
        # upcoming method transformation.
        self.viper.used_names = set()
        for sil_prog in sil_progs:
            for method in self.viper.to_list(sil_prog.methods()):
                if method.name() in used_names:
                    converted_method = self.create_method_node(
                        ctx=ctx,
                        name=method.name(),
                        args=self.viper.to_list(method.formalArgs()),
                        returns=self.viper.to_list(method.formalReturns()),
                        pres=self.viper.to_list(method.pres()),
                        posts=self.viper.to_list(method.posts()),
                        locals=self.viper.to_list(method.locals()),
                        body=method.body(),
                        position=method.pos(),
                        info=method.info(),
                    )
                    methods.append(converted_method)

        # Some obligation-related functions may only be used by the code added
        # by the method conversion we just performed, so we have to add
        # the names which have been used in the meantime. This works assuming
        # that the converted code does not introduce additional method
        # requirements (which should never be the case).
        self._add_all_used_names(used_names)

        for sil_prog in sil_progs:
            domains += [
                domain for domain in self.viper.to_list(sil_prog.domains())
                if domain.name() != 'PyType']

            function_names = [function.name() for function in functions]
            functions += [
                function
                for function in self.viper.to_list(sil_prog.functions())
                if (function.name() in used_names and
                    function.name() not in function_names)]
            predicates += self.viper.to_list(sil_prog.predicates())

        return domains, predicates, functions, methods

    def translate_program(self, modules: List[PythonModule],
                          sil_progs: List,
                          ctx: Context) -> 'silver.ast.Program':
        """
        Translates the PythonModules created by the analyzer to a Viper program.
        """
        fields = self._create_predefined_fields(ctx)
        domains = []
        predicates = []
        functions = []
        methods = []

        # Predefined obligation stuff
        obl_predicates, obl_fields = self.get_obligation_preamble(ctx)
        predicates.extend(obl_predicates)
        fields.extend(obl_fields)

        type_funcs = self.type_factory.get_default_functions(ctx)
        type_axioms = self.type_factory.get_default_axioms(ctx)

        predicate_families = OrderedDict()

        # First iteration over all modules: translate global variables, static
        # fields, and default arguments.
        for module in modules:
            ctx.module = module
            for var in module.global_vars:
                functions.append(
                    self.create_global_var_function(module.global_vars[var],
                                                    ctx))
            containers = [module]
            for class_name, cls in module.classes.items():
                if class_name in PRIMITIVES or class_name != cls.name:
                    # Skip primitives or entries for type variables.
                    continue
                containers.append(cls)
                fields += self._translate_fields(cls, ctx)
                ctx.current_class = cls
                for name, field in cls.static_fields.items():
                    functions.append(self.create_global_var_function(field,
                                                                     ctx))
            ctx.current_class = None
            # Translate default args
            for container in containers:
                for function in container.functions.values():
                    self.translate_default_args(function, ctx)
                for method in container.methods.values():
                    self.translate_default_args(method, ctx)
                for pred in container.predicates.values():
                    self.translate_default_args(pred, ctx)

        # Second iteration over all modules: Translate everything else.
        for module in modules:
            ctx.module = module

            for function in module.functions.values():
                functions.append(self.translate_function(function, ctx))
            for method in module.methods.values():
                methods.append(self.translate_method(method, ctx))
            for pred in module.predicates.values():
                predicates.append(self.translate_predicate(pred, ctx))
            for operation in module.io_operations.values():
                predicate, getters, checkers = self.translate_io_operation(
                        operation,
                        ctx)
                predicates.append(predicate)
                functions.extend(getters)
                methods.extend(checkers)
            for class_name, cls in module.classes.items():
                if class_name in PRIMITIVES or class_name != cls.name:
                    # Skip primitives and type variable entries.
                    continue
                old_class = ctx.current_class
                ctx.current_class = cls
                funcs, axioms = self.type_factory.create_type(cls, ctx)
                type_funcs.extend(funcs)
                if axioms:
                    type_axioms.extend(axioms)
                for func_name in cls.functions:
                    func = cls.functions[func_name]
                    if func.interface:
                        continue
                    functions.append(self.translate_function(func, ctx))
                    if func.overrides:
                        raise InvalidProgramException(func.node,
                                                      'invalid.override')
                for method_name in cls.methods:
                    method = cls.methods[method_name]
                    if method.interface:
                        continue
                    methods.append(self.translate_method(method, ctx))
                    if ((method_name != '__init__' or
                             (cls.superclass and
                              cls.superclass.python_class.has_classmethod)) and
                            method.overrides):
                        methods.append(self.create_override_check(method, ctx))
                for method_name in cls.static_methods:
                    method = cls.static_methods[method_name]
                    methods.append(self.translate_method(method, ctx))
                    if method.overrides:
                        methods.append(self.create_override_check(method, ctx))
                for method_name in cls.all_methods:
                    method = cls.get_method(method_name)
                    if (method.cls and method.cls != cls and
                            method_name != '__init__' and
                            method.method_type == MethodType.normal and
                            not method.interface):
                        # Inherited
                        methods.append(self.create_inherit_check(method, cls,
                                                                 ctx))
                for field_name in cls.static_fields:
                    field = cls.static_fields[field_name]
                    if cls.superclass:
                        if cls.superclass.get_static_field(field_name):
                            raise InvalidProgramException(field.node,
                                                          'invalid.override')
                for pred_name in cls.predicates:
                    pred = cls.predicates[pred_name]
                    cpred = pred
                    while cpred.overrides:
                        cpred = cpred.overrides
                    if cpred in predicate_families:
                        predicate_families[cpred].append(pred)
                    else:
                        predicate_families[cpred] = [pred]
                ctx.current_class = old_class

        for root in predicate_families:
            pf = self.translate_predicate_family(root, predicate_families[root],
                                                 ctx)
            predicates.append(pf)

        domains += [self.type_factory.create_type_domain(type_funcs,
                                                         type_axioms, ctx)]

        converted_sil_progs = self._convert_silver_elements(sil_progs, ctx)
        s_domains, s_predicates, s_functions, s_methods = converted_sil_progs
        domains += s_domains
        predicates += s_predicates
        functions += s_functions
        methods += s_methods

        prog = self.viper.Program(domains, fields, functions, predicates,
                                  methods, self.no_position(ctx),
                                  self.no_info(ctx))
        return prog

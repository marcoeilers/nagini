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
    PythonProgram,
    PythonVar
)
from py2viper_translation.lib.typedefs import (
    Expr,
    Stmt,
    StmtsAndExpr,
)
from py2viper_translation.lib.util import (
    InvalidProgramException,
    UnsupportedException,
)
from py2viper_translation.translators.abstract import Context
from py2viper_translation.translators.common import CommonTranslator
from typing import List, Tuple


class ProgramTranslator(CommonTranslator):

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
        stmt, value = self.translate_expr(var.value, ctx)
        if stmt:
            raise InvalidProgramException('purity.violated', var.node)
        posts.append(
            self.viper.EqCmp(result, value, position, self.no_info(ctx)))
        return self.viper.Function(var.sil_name, [], type, [], posts, None,
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
        params = []
        results = []
        args = []
        locals_before = set(method.locals.values())
        if method.type:
            results.append(method.result.decl)

        error_var = PythonVar(ERROR_NAME, None,
                              ctx.program.global_prog.classes['Exception'])
        error_var.process(ERROR_NAME, self.translator)
        optional_error_var = error_var if method.declared_exceptions else None

        if method.declared_exceptions:
            results.append(error_var.decl)

        mname = ctx.program.get_fresh_name(cls.name + '_' + method.name +
                                           '_inherit_check')
        pres, posts = self.extract_contract(method, ERROR_NAME,
                                            False, ctx)
        if method.method_type == MethodType.normal:
            not_null = self.viper.NeCmp(next(iter(method.args.values())).ref(),
                                        self.viper.NullLit(self.no_position(ctx),
                                                           self.no_info(ctx)),
                                        self.no_position(ctx), self.no_info(ctx))
            new_type = self.type_factory.concrete_type_check(
                next(iter(method.args.values())).ref(), cls, pos, ctx)
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
        body = self.translate_block(stmts, self.no_position(ctx),
                                    self.no_info(ctx))
        locals_after = set(method.locals.values())
        locals_diff = locals_after.symmetric_difference(locals_before)
        locals = [var.decl for var in locals_diff]
        ctx.current_function = old_function
        result = self.viper.Method(mname, params, results, pres, posts, locals,
                                   body, self.no_position(ctx),
                                   self.no_info(ctx))
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
        params = []
        args = []

        mname = ctx.program.get_fresh_name(method.sil_name + '_override_check')
        pres, posts = self.extract_contract(method.overrides, '_err',
                                            False, ctx)
        self_arg = method.overrides.args[next(iter(method.overrides.args))]
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
        if method.cls:
            not_null = self.viper.NeCmp(next(iter(method.args.values())).ref(),
                                        self.viper.NullLit(self.no_position(ctx),
                                                           self.no_info(ctx)),
                                        self.no_position(ctx),
                                        self.no_info(ctx))
            pres = [not_null] + pres
        for arg in method.overrides.args:
            params.append(method.overrides.args[arg].decl)
            args.append(method.overrides.args[arg].ref())

        has_subtype = self.var_type_check(self_arg.sil_name, method.cls, pos,
                                          ctx, inhale_exhale=False)
        called_name = method.sil_name
        ctx.position.pop()
        results, targets, body = self._create_override_check_body_impure(
            method, has_subtype, called_name, args, ctx)
        ctx.current_function = old_function
        result = self.viper.Method(mname, params, results, pres, posts, [],
                                   body, self.no_position(ctx),
                                   self.no_info(ctx))

        self.info = None
        return result

    def _create_override_check_body_impure(self, method: PythonMethod,
            has_subtype: Expr, calledname: str,
            args: List[Expr], ctx: Context) -> Tuple[List['ast.LocalVarDecl'],
                                                     List['ast.LocalVar'],
                                                     Stmt]:
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

        # check that arg names match and default args are equal
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
        call = self.viper.MethodCall(calledname, args, targets,
                                     self.to_position(method.node, ctx),
                                     self.no_info(ctx))
        ctx.position.pop()
        subtype_assume = self.viper.Inhale(has_subtype, self.no_position(ctx),
                                           self.no_info(ctx))
        body = default_checks + [subtype_assume, call]
        body_block = self.translate_block(body, self.no_position(ctx),
                                          self.no_info(ctx))
        return results, targets, body_block

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
                    raise InvalidProgramException(arg.default, 'purity.violated')
                arg.default_expr = expr

    def translate_program(self, programs: List[PythonProgram],
                          sil_progs: List,
                          ctx: Context) -> 'silver.ast.Program':
        """
        Translates a PythonProgram created by the analyzer to a Viper program.
        """
        domains = []
        fields = []
        functions = []
        predicates = []
        methods = []

        for sil_prog in sil_progs:
            domains += [d for d in self.viper.to_list(sil_prog.domains())
                        if d.name() != 'PyType']
            functions += self.viper.to_list(sil_prog.functions())
            predicates += self.viper.to_list(sil_prog.predicates())
            methods += self.viper.to_list(sil_prog.methods())

        # predefined fields
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

        type_funcs = self.type_factory.get_default_functions(ctx)
        type_axioms = self.type_factory.get_default_axioms(ctx)

        predicate_families = OrderedDict()

        for program in programs:
            ctx.program = program
            for var in program.global_vars:
                functions.append(
                    self.create_global_var_function(program.global_vars[var], ctx))

            for class_name, cls in program.classes.items():
                if class_name in PRIMITIVES:
                    continue
                fields += self._translate_fields(cls, ctx)
                for name, field in cls.static_fields.items():
                    functions.append(self.create_global_var_function(field, ctx))

            # translate default args
            containers = [program] + list(program.classes.values())
            for container in containers:
                for function in container.functions.values():
                    self.translate_default_args(function, ctx)
                for method in container.methods.values():
                    self.translate_default_args(method, ctx)
                for pred in container.predicates.values():
                    self.translate_default_args(pred, ctx)

            for function in program.functions.values():
                functions.append(self.translate_function(function, ctx))
            for method in program.methods.values():
                methods.append(self.translate_method(method, ctx))
            for pred in program.predicates.values():
                predicates.append(self.translate_predicate(pred, ctx))
            for class_name, cls in program.classes.items():
                if class_name in PRIMITIVES:
                    continue
                old_class = ctx.current_class
                ctx.current_class = cls
                funcs, axioms = self.type_factory.create_type(cls, ctx)
                type_funcs.append(funcs)
                if axioms:
                    type_axioms.append(axioms)
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
                              cls.superclass.has_classmethod)) and
                            method.overrides):
                        methods.append(self.create_override_check(method, ctx))
                for method_name in cls.get_all_methods():
                    method = cls.get_method(method_name)
                    if (method.cls and method.cls != cls and
                            method_name != '__init__' and
                            method.method_type == MethodType.normal):
                        # inherited
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
                # methods.append(self.create_constructor(cls))
                ctx.current_class = old_class

        for root in predicate_families:
            pf = self.translate_predicate_family(root, predicate_families[root],
                                                 ctx)
            predicates.append(pf)

        domains += [self.type_factory.create_type_domain(type_funcs,
                                                         type_axioms, ctx)]

        prog = self.viper.Program(domains, fields, functions, predicates,
                                  methods, self.no_position(ctx),
                                  self.no_info(ctx))
        return prog

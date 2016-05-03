import ast

from collections import OrderedDict
from py2viper_translation.lib.constants import (
    ERROR_NAME,
    PRIMITIVES,
    RESULT_NAME
)
from py2viper_translation.lib.program_nodes import (
    PythonClass,
    PythonField,
    PythonMethod,
    PythonProgram,
    PythonVar
)
from py2viper_translation.lib.util import (
    InvalidProgramException
)
from py2viper_translation.translators.abstract import (
    CommonTranslator,
    Context,
    Expr,
    Stmt
)
from typing import List, Tuple


class ProgramTranslator(CommonTranslator):

    def translate_field(self, field: PythonField,
                        ctx: Context) -> 'silver.ast.Field':
        return self.viper.Field(field.sil_name,
                                self.translate_type(field.type, ctx),
                                self.to_position(field.node, ctx),
                                self.no_info(ctx))

    def create_global_var_function(self, var: PythonVar,
                                   ctx: Context) -> 'silver.ast.Function':
        """
        Creates a Viper function representing the given global variable.
        """
        type = self.translate_type(var.type, ctx)
        if type == self.viper.Ref:
            raise UnsupportedException(var.node)
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
        assert ctx.position is None
        ctx.position = self.viper.to_position(cls.node)
        self.info = self.viper.SimpleInfo(['behavioural.subtyping'])
        params = []
        results = []
        args = []
        locals_before = set(method.locals.values())
        if method.type:
            results.append(method.result.decl)

        error_var = PythonVar(ERROR_NAME, None, ctx.program.classes['Exception'])
        error_var.process(ERROR_NAME, self.translator)
        optional_error_var = error_var if method.declared_exceptions else None

        if method.declared_exceptions:
            results.append(error_var.decl)

        mname = ctx.program.get_fresh_name(cls.name + '_' + method.name +
                                           '_inherit_check')
        pres, posts = self.extract_contract(method, ERROR_NAME,
                                            False, ctx)
        not_null = self.viper.NeCmp(next(iter(method.args.values())).ref,
                                    self.viper.NullLit(self.no_position(ctx),
                                                       self.no_info(ctx)),
                                    self.no_position(ctx), self.no_info(ctx))
        new_type = self.type_factory.concrete_type_check(
            next(iter(method.args.values())).ref, cls, ctx)
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
        ctx.position = None
        self.info = None
        return result

    def create_override_check(self, method: PythonMethod,
                              ctx: Context) -> 'silver.ast.Callable':
        """
        Creates a Viper function/method with the contract of the overridden
        function which calls the overriding function, to check behavioural
        subtyping.
        """
        old_function = ctx.current_function
        ctx.current_function = method.overrides
        assert ctx.position is None
        ctx.position = self.viper.to_position(method.node)
        self.info = self.viper.SimpleInfo(['behavioural.subtyping'])
        self._check_override_validity(method, ctx)
        params = []
        args = []

        mname = ctx.program.get_fresh_name(method.sil_name + '_override_check')
        pres, posts = self.extract_contract(method.overrides, '_err',
                                            False, ctx)
        if method.cls:
            not_null = self.viper.NeCmp(next(iter(method.args.values())).ref,
                                        self.viper.NullLit(self.no_position(ctx),
                                                           self.no_info(ctx)),
                                        self.no_position(ctx),
                                        self.no_info(ctx))
            pres = [not_null] + pres
        for arg in method.overrides.args:
            params.append(method.overrides.args[arg].decl)
            args.append(method.overrides.args[arg].ref)
        self_arg = method.overrides.args[next(iter(method.overrides.args))]
        has_subtype = self.var_type_check(self_arg.sil_name, method.cls, True,
                                          ctx)
        called_name = method.sil_name
        if method.pure:
            pres = pres + [has_subtype]
            formal_args = []
            for arg in method.args:
                formal_args.append(method.args[arg].decl)
            type = self.translate_type(method.type, ctx)
            func_app = self.viper.FuncApp(called_name, args,
                                          self.no_position(ctx),
                                          self.no_info(ctx), type, formal_args)
            ctx.current_function = old_function
            result = self.viper.Function(mname, params, type, pres, posts,
                                         func_app, self.no_position(ctx),
                                         self.no_info(ctx))
            ctx.position = None
            self.info = None
            return result
        else:
            results, targets, body = self._create_override_check_body_impure(
                method, has_subtype, called_name, args, ctx)
            ctx.current_function = old_function
            result = self.viper.Method(mname, params, results, pres, posts, [],
                                       body, self.no_position(ctx),
                                       self.no_info(ctx))
            ctx.position = None
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
        call = self.viper.MethodCall(calledname, args, targets,
                                     self.no_position(ctx),
                                     self.no_info(ctx))
        subtype_assume = self.viper.Inhale(has_subtype, self.no_position(ctx),
                                           self.no_info(ctx))
        body = [subtype_assume, call]
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
        for exc in method.declared_exceptions:
            exc_class = ctx.program.classes[exc]
            allowed = False
            for superexc in method.overrides.declared_exceptions:
                superexcclass = ctx.program.classes[superexc]
                if exc_class.issubtype(superexcclass):
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

    def translate_program(self, program: PythonProgram,
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
            domains += self.viper.to_list(sil_prog.domains())
            fields += self.viper.to_list(sil_prog.fields())
            functions += self.viper.to_list(sil_prog.functions())
            predicates += self.viper.to_list(sil_prog.predicates())
            methods += self.viper.to_list(sil_prog.methods())

        type_funcs = self.type_factory.get_default_functions(ctx)
        type_axioms = self.type_factory.get_default_axioms(ctx)

        predicate_families = OrderedDict()

        for var in program.global_vars:
            functions.append(
                self.create_global_var_function(program.global_vars[var], ctx))

        for class_name in program.classes:
            if class_name in PRIMITIVES:
                continue
            cls = program.classes[class_name]
            for field_name in cls.fields:
                field = cls.fields[field_name]
                if field.inherited is None:
                    sil_field = self.translate_field(field, ctx)
                    field.sil_field = sil_field
                    fields.append(sil_field)

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
                if method_name != '__init__' and method.overrides:
                    methods.append(self.create_override_check(method, ctx))
            for method_name in cls.get_all_methods():
                method = cls.get_method(method_name)
                if (method.cls != cls and method_name != '__init__' and
                        not cls.name.startswith('Dummy_Sub')):
                    # inherited
                    methods.append(self.create_inherit_check(method, cls, ctx))
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

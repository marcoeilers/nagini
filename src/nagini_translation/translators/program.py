"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import ast
from collections import OrderedDict
from typing import List, Set, Tuple

from nagini_translation.lib.constants import (
    ARBITRARY_BOOL_FUNC,
    ASSERTING_FUNC,
    CHECK_DEFINED_FUNC,
    ERROR_NAME,
    FUNCTION_DOMAIN_NAME,
    GET_ARG_FUNC,
    GET_METHOD_FUNC,
    GET_OLD_FUNC,
    GLOBAL_VAR_FIELD,
    IS_DEFINED_FUNC,
    JOINABLE_FUNC,
    MAY_SET_PRED,
    METHOD_ID_DOMAIN,
    NAME_DOMAIN,
    PRIMITIVES,
    RESULT_NAME,
    THREAD_DOMAIN,
    THREAD_POST_PRED,
    THREAD_START_PRED,
)
from nagini_translation.lib.program_nodes import (
    MethodType,
    PythonClass,
    PythonField,
    PythonMethod,
    PythonModule,
    PythonNode,
    PythonVar,
)
from nagini_translation.lib.typedefs import (
    Domain,
    DomainAxiom,
    DomainFunc,
    DomainType,
    Expr,
    Field,
    Function,
    Info,
    Method,
    Position,
    Predicate,
    Program,
    Stmt,
    Var,
    VarDecl,
)
from nagini_translation.lib.util import (
    InvalidProgramException,
)
from nagini_translation.sif.lib.viper_ast_extended import ViperASTExtended
from nagini_translation.translators.abstract import Context
from nagini_translation.translators.common import CommonTranslator


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

    def _translate_fields(self, cls: PythonClass, all_names,
                          ctx: Context) -> Tuple[List['silver.ast.Field'],
                                                 List['silver.ast.Function'],
                                                 List['silver.ast.Method']]:
        """
        Translates fields and properties to Viper. Normal fields get translated to
        Viper fields, properties to functions and property setters to methods.
        """
        fields = []
        functions = []
        methods = []
        for field in cls.fields.values():
            if isinstance(field, PythonField) and field.inherited is None:
                sil_field = self.translate_field(field, ctx)
                field.sil_field = sil_field
                fields.append(sil_field)
            elif isinstance(field, PythonMethod):
                # This is a property
                if cls.module is not cls.module.global_module:
                    all_names.append(field.sil_name)
                used_names = set()
                self.viper.used_names = used_names
                self.viper.used_names_sets[field.sil_name] = used_names
                if field.overrides:
                    raise InvalidProgramException(field.node, 'invalid.override')
                getter = self.translate_function(field, ctx)
                functions.append(getter)
                if field.setter:
                    used_names = set()
                    self.viper.used_names = used_names
                    self.viper.used_names_sets[field.setter.sil_name] = used_names
                    setter = self.translate_method(field.setter, ctx)
                    if cls.module is not cls.module.global_module:
                        all_names.append(field.setter.sil_name)
                    methods.append(setter)

        return fields, functions, methods

    def create_static_field_function(self, root: PythonVar,
                                     classes: List[PythonClass],
                                     ctx: Context) -> 'silver.ast.Function':
        """
        Creates a function which represents a static field. The function takes
        a parameter which represents the class on which it is called, and has
        postconditions defining its return value based on this parameter.

        'root' must be the version of the field in the class that is highest in
        the inheritance hierarchy. 'classes' must be a list of classes that
        inherit or redefine it.
        """
        current_module = ctx.module
        type = self.translate_type(root.type, ctx)
        position = self.to_position(root.node, ctx)
        info = self.no_info(ctx)
        posts = []
        result = self.viper.Result(type, position, info)
        type_type = self.type_factory.type_type()
        type_decl = self.viper.LocalVarDecl('receiver', type_type, position,
                                            info)
        type_ref = self.viper.LocalVar('receiver', type_type, position, info)
        if root.type.name not in PRIMITIVES:
            posts.append(self.type_check(result, root.type, position, ctx))
        # Iterate through all classes that 'inherit' or redefine this field
        for cls in classes:
            # Get their version (might be redefined or inherited).
            field = cls.get_static_field(root.name)
            ctx.current_class = field.cls
            ctx.module = field.cls.module
            # Compute the field value
            stmt, value = self.translate_expr(field.value, ctx)
            if stmt:
                raise InvalidProgramException('purity.violated', field.node)
            field_position = self.to_position(field.node, ctx)
            # Create a postcondition of the form
            # receiver == cls ==> result == value
            has_value = self.viper.EqCmp(result, value, field_position, info)
            type_literal = self.type_factory.translate_type_literal(
                field.cls, field_position, ctx)
            exact_type = self.viper.EqCmp(type_ref, type_literal, position,
                                          info)
            posts.append(self.viper.Implies(exact_type, has_value,
                                            field_position, info))
        ctx.module = current_module
        # Create a single function that represents all
        return self.viper.Function(root.sil_name, [type_decl], type, [], posts,
                                   None, position, info)

    def create_global_var_function(self, var: PythonVar,
                                   ctx: Context) -> 'silver.ast.Function':
        """
        Creates a Viper function representing the given global variable.
        """
        type = self.translate_type(var.type, ctx)
        position = self.to_position(var.node, ctx)
        posts = []
        result = self.viper.Result(type, position, self.no_info(ctx))
        if var.is_final:
            if var.type.name not in PRIMITIVES:
                posts.append(self.type_check(result, var.type, position, ctx))
            if hasattr(var, 'value'):
                body = None
                try:
                    stmt, value = self.translate_expr(var.value, ctx)
                    if not stmt:
                        if not self.viper.is_heap_dependent(value):
                            body = value
                            posts.append(self.viper.EqCmp(result, value, position,
                                                          self.no_info(ctx)))
                except AttributeError as e:
                    # The translation (probably) tried to access ctx.current_function
                    pass
            else:
                body = None
        else:
            body = None
        return self.viper.Function(var.sil_name, [], type, [], posts, body,
                                   self.to_position(var.node, ctx),
                                   self.no_info(ctx))

    def _create_inherit_check_postamble(self, stmts: List[Stmt], end_lbl: 'silver.ast.Label',
                                        ctx: Context) -> None:
        goto_end = self.viper.Goto(end_lbl.name(), self.no_position(ctx),
                                   self.no_info(ctx))
        stmts.append(goto_end)
        stmts += self.add_handlers_for_inlines(ctx)

        stmts.append(end_lbl)

    def create_inherit_check(self, method: PythonMethod, cls: PythonClass,
                             ctx: Context) -> 'silver.ast.Callable':
        """
        Creates a Viper function/method with the contract of the overridden
        function which calls the overriding function, to check behavioural
        subtyping.
        """
        old_function = ctx.current_function
        ctx.current_function = method
        pos = self.viper.to_position(cls.node, ctx.position, py_node=method)
        ctx.position.append(('inheritance', pos))
        self.info = self.viper.SimpleInfo(['behavioural.subtyping'])

        args = []
        params = []

        for arg_name, arg in method.args.items():
            args.append(arg)
            params.append(arg.decl)

        self.bind_type_vars(method, ctx)

        results = []
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
        self.viper.used_names_sets[method.sil_name].add(mname)
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

        stmts, end_lbl = self.inline_method(method, args, method.result,
                                            error_var, ctx)

        self._create_inherit_check_postamble(stmts, end_lbl, ctx)

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
        pos = self.viper.to_position(method.node, ctx.position, py_node=method)
        ctx.position.append(('override', pos))
        self.info = self.viper.SimpleInfo(['behavioural.subtyping'])
        self._check_override_validity(method, ctx)

        params = []
        args = []

        for arg in method.overrides.args:
            params.append(method.overrides.args[arg].decl)
            args.append(method.overrides.args[arg].ref())

        self.bind_type_vars(method.overrides, ctx)

        mname = ctx.module.get_fresh_name(method.sil_name + '_override_check')
        self.viper.used_names_sets[method.sil_name].add(mname)
        pres, posts = self.extract_contract(method.overrides, '_err',
                                            False, ctx)
        self_arg = None
        has_subtype = None
        if method.cls and method.method_type == MethodType.normal:
            self_arg = method.overrides.args[next(iter(method.overrides.args))]
            not_null = self.viper.NeCmp(next(iter(method.overrides.args.values())).ref(),
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
            cls_arg = next(iter(method.overrides.args.values())).ref()
            has_subtype = self.type_factory.subtype_check(cls_arg, method.cls,
                                                          pos, ctx)
        if method.name == '__init__':
            fields = method.cls.all_fields
            pres.extend([self.get_may_set_predicate(self_arg.ref(), f, ctx)
                         for f in fields])

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
                                                    ctx.position, py_node=method)))
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
        definition_deps = method.definition_deps
        if method.cls:
            definition_deps = method.cls.definition_deps
        for arg in method.args.values():
            if (arg.node and arg.node.annotation and
                    not isinstance(arg.node.annotation, (ast.Str, ast.NameConstant))):
                type = self.get_target(arg.node.annotation, ctx)
                if type and not type.python_class.interface:
                    definition_deps.add((arg.node.annotation, type.python_class,
                                         method.module))
            if arg.default:
                stmt, expr = self.translate_expr(arg.default, ctx)
                if not stmt and expr:
                    arg.default_expr = expr
        if (method.node and method.node.returns and
                not isinstance(method.node.returns, (ast.Str, ast.NameConstant))):
            type = self.get_target(method.node.returns, ctx)
            if type and not type.python_class.interface:
                definition_deps.add((method.node.returns, type.python_class,
                                     method.module))


    def _create_predefined_fields(self,
                                  ctx: Context) -> List[Field]:
        """
        Creates and returns fields needed for encoding various language
        features, e.g. collections, measures and iterators.
        """
        fields = []
        fields.append(self.viper.Field(GLOBAL_VAR_FIELD, self.viper.Ref,
                                       self.no_position(ctx),
                                       self.no_info(ctx)))
        fields.append(self.viper.Field('__container', self.viper.Ref,
                                       self.no_position(ctx),
                                       self.no_info(ctx)))
        fields.append(self.viper.Field('__iter_index', self.viper.Int,
                                       self.no_position(ctx),
                                       self.no_info(ctx)))
        fields.append(self.viper.Field('__previous', self.viper.SeqType(self.viper.Ref),
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
        fields.append(self.viper.Field('dict_acc2',
                                       self.viper.Ref,
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

    def _convert_silver_elements(
            self, sil_progs: Program, all_used: List[str], include_names_domain: bool,
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

        if all_used:
            used_names = set(all_used)
            self.viper.used_names = set()
        else:
            used_names = set()
            self._add_all_used_names(used_names)

        # Reset used names set, we only need the additional ones used by the
        # upcoming method transformation.
        self.viper.used_names = set()
        for method in self.viper.to_list(sil_progs.methods()):
            if method.name() in used_names:
                body = self.viper.from_option(method.body())
                converted_method = self.create_method_node(
                    ctx=ctx,
                    name=method.name(),
                    args=self.viper.to_list(method.formalArgs()),
                    returns=self.viper.to_list(method.formalReturns()),
                    pres=self.viper.to_list(method.pres()),
                    posts=self.viper.to_list(method.posts()),
                    locals=[],
                    body=body,
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

        excluded_domains = ('PyType', NAME_DOMAIN) if not include_names_domain else ('PyType',)
        domains += [
            domain for domain in self.viper.to_list(sil_progs.domains())
            if domain.name() not in excluded_domains]

        functions += [
            function
            for function in self.viper.to_list(sil_progs.functions())
            if function.name() in used_names]
        predicates += self.viper.to_list(sil_progs.predicates())

        return domains, predicates, functions, methods

    def track_dependencies(self, selected_names: List[str], selected: Set[str],
                           node: PythonNode, ctx: Context) -> None:
        """
        If specific parts of the program have been selected to be verified,
        marks that the given PythonNode is about to be translated, s.t. it can
        be tracked which other elements are referenced by the translation of
        this node. Also checks if the given element is among those selected
        to be verified, and adds its Silver name to the list of selected Silver
        names later used when computing which parts of the program to give to
        Viper.
        """
        if node.sil_name in self.viper.used_names_sets:
            used_names = self.viper.used_names_sets[node.sil_name]
        else:
            used_names = set()
        self.viper.used_names = used_names
        self.viper.used_names_sets[node.sil_name] = used_names
        if selected_names is None:
            return
        if (node.name in selected or
                (hasattr(node, 'cls') and node.cls and
                 node.cls.name + '.' + node.name in selected)):
            selected_names.append(node.sil_name)

    def create_functions_domain(self, constants: List, ctx: Context):
        return self.viper.Domain(FUNCTION_DOMAIN_NAME, constants, [], [],
                                 self.no_position(ctx), self.no_info(ctx))

    def translate_function_constant(self, func: PythonMethod, ctx: Context):
        func_type = self.viper.function_domain_type()
        return self.viper.DomainFunc(func.func_constant, [], func_type, True,
                                     self.to_position(func.node, ctx), self.no_info(ctx),
                                     FUNCTION_DOMAIN_NAME)

    def create_joinable_function(self, ctx: Context) -> Function:
        thread_arg_decl = self.viper.LocalVarDecl('t', self.viper.Ref,
                                                  self.no_position(ctx),
                                                  self.no_info(ctx))
        return self.viper.Function(JOINABLE_FUNC, [thread_arg_decl], self.viper.Bool,
                                   [], [], None, self.no_position(ctx), self.no_info(ctx))

    def create_thread_predicates(self, ctx: Context) -> Function:
        thread_arg_decl = self.viper.LocalVarDecl('t', self.viper.Ref,
                                                  self.no_position(ctx),
                                                  self.no_info(ctx))
        post_pred =  self.viper.Predicate(THREAD_POST_PRED, [thread_arg_decl], None,
                                          self.no_position(ctx), self.no_info(ctx))
        start_pred = self.viper.Predicate(THREAD_START_PRED, [thread_arg_decl], None,
                                          self.no_position(ctx), self.no_info(ctx))
        return [start_pred, post_pred]

    def create_method_id_domain(self, constants: List['silver.ast.DomainFunc'],
                                ctx: Context) -> 'silver.ast.Domain':
        return self.viper.Domain(METHOD_ID_DOMAIN, constants, [], [],
                                 self.no_position(ctx), self.no_info(ctx))

    def translate_method_id_to_constant(self, method, ctx) -> 'silver.ast.DomainFunc':
        func_type = self.viper.DomainType(METHOD_ID_DOMAIN, {}, [])
        return self.viper.DomainFunc(method.threading_id,[],func_type, True,
                                     self.to_position(method.node,ctx), self.no_info(ctx),
                                     METHOD_ID_DOMAIN)

    def create_thread_domain(self, ctx: Context) -> 'silver.ast.Domain':
        pos, info = self.no_position(ctx), self.no_info(ctx)
        method_id_type = self.viper.DomainType(METHOD_ID_DOMAIN, {}, [])
        thread_param = self.viper.LocalVarDecl('t', self.viper.Ref, pos, info)
        index_param = self.viper.LocalVarDecl('i', self.viper.Int, pos, info)
        get_method = self.viper.DomainFunc(GET_METHOD_FUNC, [thread_param],
                                           method_id_type, False, pos, info,
                                           THREAD_DOMAIN)
        get_arg = self.viper.DomainFunc(GET_ARG_FUNC, [thread_param, index_param],
                                        self.viper.Ref, False, pos, info, THREAD_DOMAIN)
        get_old = self.viper.DomainFunc(GET_OLD_FUNC, [thread_param, index_param],
                                       self.viper.Ref, False, pos, info, THREAD_DOMAIN)
        domain = self.viper.Domain(THREAD_DOMAIN, [get_method, get_arg, get_old], [], [],
                                   pos, info)
        if isinstance(self.viper, ViperASTExtended):
            getattr(getattr(self.viper.ast_extensions, 'SIFExtendedTransformer$'), 'MODULE$').addDomainFuncToDuplicate(
                self.viper.to_seq([get_method, get_arg, get_old]))
        return domain

    def create_definedness_functions(self, ctx: Context) -> List['silver.ast.Function']:
        pos = self.no_position(ctx)
        info = self.no_info(ctx)
        id_param_decl = self.viper.LocalVarDecl('id', self.viper.Int, pos, info)
        id_param = self.viper.LocalVar('id', self.viper.Int, pos, info)
        is_defined_func = self.viper.Function(IS_DEFINED_FUNC, [id_param_decl],
                                              self.viper.Bool, [], [], None, pos, info)
        var_param_decl = self.viper.LocalVarDecl('val', self.viper.Ref, pos, info)
        var_param = self.viper.LocalVar('val', self.viper.Ref, pos, info)
        is_defined_pre = self.viper.FuncApp(IS_DEFINED_FUNC, [id_param], pos, info,
                                            self.viper.Bool, [id_param_decl])
        check_defined_func = self.viper.Function(CHECK_DEFINED_FUNC,
                                                 [var_param_decl, id_param_decl],
                                                 self.viper.Ref, [is_defined_pre], [],
                                                 var_param, pos, info)
        return [is_defined_func, check_defined_func]

    def create_asserting_function(self,
                                            ctx: Context) -> List['silver.ast.Function']:
        pos = self.no_position(ctx)
        info = self.no_info(ctx)
        var_param_decl = self.viper.LocalVarDecl('val', self.viper.Ref, pos, info)
        var_param = self.viper.LocalVar('val', self.viper.Ref, pos, info)
        assertion_param_decl = self.viper.LocalVarDecl('ass', self.viper.Bool, pos, info)
        assertion_param = self.viper.LocalVar('ass', self.viper.Bool, pos, info)
        asserting_func = self.viper.Function(ASSERTING_FUNC,
                                             [var_param_decl, assertion_param_decl],
                                             self.viper.Ref, [assertion_param], [],
                                             var_param, pos, info)
        return [asserting_func]

    def create_arbitrary_bool_func(self, ctx: Context) -> 'silver.ast.Function':
        pos = self.no_position(ctx)
        info = self.no_info(ctx)
        i_param_decl = self.viper.LocalVarDecl('i', self.viper.Int, pos, info)
        return self.viper.Function(ARBITRARY_BOOL_FUNC, [i_param_decl],
                                   self.viper.Bool, [], [], None, pos, info)

    def create_may_set_predicate(self, ctx: Context) -> 'silver.ast.Predicate':
        pos = self.no_position(ctx)
        info = self.no_info(ctx)
        receiver_param_decl = self.viper.LocalVarDecl('rec', self.viper.Ref, pos, info)
        id_param_decl = self.viper.LocalVarDecl('id', self.viper.Int, pos, info)
        may_set_pred = self.viper.Predicate(MAY_SET_PRED,
                                            [receiver_param_decl, id_param_decl], None,
                                            pos, info)
        return may_set_pred

    def _get_adt_cons_params_decl(self, cons: PythonClass, adt_name: str,
                                  adt_type: DomainType, pos: Position,
                                 info: Info, ctx: Context) -> List[VarDecl]:
        """
        Returns the parameters of the ADT constructor as a list of variable
        declarations.
        """
        arguments = []
        for i, arg_type in enumerate(cons.fields.values()):
            if arg_type.type.name == adt_name:
                argument_type = adt_type
            else:
                argument_type = self.translate_type(arg_type.type, ctx)
            argument = self.viper.LocalVarDecl('_arg' + str(i), argument_type, pos, info)
            arguments.append(argument)
        return arguments

    def _get_adt_cons_params_use(self, cons: PythonClass, adt_name: str,
                                 adt_type: DomainType, pos: Position,
                                 info: Info, ctx: Context) -> List[Var]:
        """
        Returns the parameters of the ADT constructor as a list of variables.
        """
        arguments = []
        for i, arg_type in enumerate(cons.fields.values()):
            if arg_type.type.name == adt_name:
                argument_type = adt_type
            else:
                argument_type = self.translate_type(arg_type.type, ctx)
            argument = self.viper.LocalVar('_arg' + str(i), argument_type, pos, info)
            arguments.append(argument)
        return arguments

    def _conjoin(self, eqs: List[Expr], pos: Position, info: Info) -> Expr:
        """
        Conjoin all expressions in the list.
        """
        return eqs[0] if len(eqs) == 1 else self.viper.And(eqs[0],
               self._conjoin(eqs[1:], pos, info), pos, info)

    def _disjoin(self, eqs: List[Expr], pos: Position, info: Info) -> Expr:
        """
        Disjoin all expressions in the list.
        """
        return eqs[0] if len(eqs) == 1 else self.viper.Or(eqs[0],
               self._disjoin(eqs[1:], pos, info), pos, info)

    def _create_adt_func_constructors(self, adt: PythonClass, adt_type: DomainType,
                                      pos: Position, info: Info,
                                      ctx: Context) -> List[DomainFunc]:
        """
        Create domain functions representing constructors of the ADT.
        """
        assert adt.all_subclasses[0] == adt
        for cons in adt.all_subclasses[1:]:
            arguments = self._get_adt_cons_params_decl(cons, adt.name, adt_type, pos,
                                                       info, ctx)
            yield self.viper.DomainFunc(adt.fresh(adt.adt_prefix + cons.name),
                                        arguments, adt_type, False, pos, info,
                                        adt.adt_domain_name)
    
    def _create_adt_func_deconstructors(self, adt: PythonClass, adt_type: DomainType,
                                        pos: Position, info: Info,
                                        ctx: Context) -> List[DomainFunc]:
        """
        Create domain functions representing deconstructors of the ADT.
        """
        adt_obj_decl = self.viper.LocalVarDecl('obj', adt_type, pos, info)
        for cons in adt.all_subclasses[1:]:
            for arg_name, arg_type in cons.fields.items():
                if arg_type.type.name == adt.name:
                    function_type = adt_type
                else:
                    function_type = self.translate_type(arg_type.type, ctx)
                yield self.viper.DomainFunc(adt.fresh(adt.adt_prefix + cons.name
                                            + '_' + arg_name), [adt_obj_decl],
                                            function_type, False, pos, info,
                                            adt.adt_domain_name)

    def _create_adt_func_constructor_types(self, adt: PythonClass, adt_type: DomainType,
                                           pos: Position, info: Info) -> List[DomainFunc]:
        """
        Create domain function representing the constructor types of the ADT.
        """
        # Given the ADT, return the constructor used to create it
        adt_obj_decl = self.viper.LocalVarDecl('obj', adt_type, pos, info)
        yield self.viper.DomainFunc(adt.fresh(adt.adt_prefix + 'cons_type'),
                                    [adt_obj_decl], self.viper.Int, False,
                                    pos, info, adt.adt_domain_name)

        # Create a constant for each constructor
        for cons in adt.all_subclasses[1:]:
            yield self.viper.DomainFunc(adt.fresh(adt.adt_prefix + cons.name +
                                        '_type'), [], self.viper.Int, True, pos,
                                        info, adt.adt_domain_name)

        # Create a boolean function for each type
        for cons in adt.all_subclasses[1:]:
            yield self.viper.DomainFunc(adt.fresh(adt.adt_prefix + 'is_' +
                                        cons.name), [adt_obj_decl],
                                        self.viper.Bool, False, pos, info,
                                        adt.adt_domain_name)


    def _create_adt_equality_axioms(self, adt: PythonClass,
                                    adt_type: DomainType, pos: Position,
                                    info: Info, ctx: Context) -> List[DomainAxiom]:
        for cons in adt.all_subclasses[1:]:
            args = self._get_adt_cons_params_use(cons, adt.name, adt_type, pos, info, ctx)
            args_decl = self._get_adt_cons_params_decl(cons, adt.name, adt_type, pos,
                                                       info, ctx)
            args_2 = [self.viper.LocalVar('__' + v.name(), v.typ(), pos, info) for v in args]
            args_decl_2 = [self.viper.LocalVarDecl('__' + v.name(), v.typ(), pos, info) for
                           v in args_decl]
            if len(args) > 0:
                cons_call = self.viper.DomainFuncApp(adt.fresh(adt.adt_prefix +
                                                               cons.name), args, adt_type,
                                                     pos, info, adt.adt_domain_name)
                cons_call_2 = self.viper.DomainFuncApp(adt.fresh(adt.adt_prefix +
                                                                 cons.name), args_2, adt_type,
                                                       pos, info, adt.adt_domain_name)
                cons_equal = self.viper.EqCmp(cons_call, cons_call_2, pos, info)
                args_equal = [self.viper.EqCmp(first, second, pos, info)
                              for (first, second) in zip(args, args_2)]
                args_equal = self._conjoin(args_equal, pos, info)
                both_equal = self.viper.EqCmp(cons_equal, args_equal, pos, info)
                trigger = self.viper.Trigger([cons_call, cons_call_2], pos, info)
                quant = self.viper.Forall(args_decl + args_decl_2, [trigger], both_equal,
                                          pos, info)
                yield self.viper.DomainAxiom(adt.fresh(adt.adt_prefix +
                                                       'equals_' + cons.name),
                                             quant, pos, info, adt.adt_domain_name)


    def _create_adt_axiom_deconstructors_over_constructors(self, adt: PythonClass,
                                      adt_type: DomainType, pos: Position,
                                      info: Info, ctx: Context) -> List[DomainAxiom]:
        """
        Create domain axiom representing the distribution of deconstructors over
        constructors.
        """
        for cons in adt.all_subclasses[1:]:
            args = self._get_adt_cons_params_use(cons, adt.name, adt_type, pos, info, ctx)
            args_decl = self._get_adt_cons_params_decl(cons, adt.name, adt_type, pos,
                                                       info, ctx)
            if len(args) > 0:
                cons_call = self.viper.DomainFuncApp(adt.fresh(adt.adt_prefix +
                                                     cons.name), args, adt_type,
                                                     pos, info, adt.adt_domain_name)
                foralls = []
                for (arg_name, _), arg in zip(cons.fields.items(), args):
                    decons_call = self.viper.DomainFuncApp(adt.fresh(adt.adt_prefix +
                                                           cons.name + '_' + arg_name),
                                                           [cons_call], arg.typ(), pos,
                                                           info, adt.adt_domain_name)
                    eq = self.viper.EqCmp(decons_call, arg, pos, info)
                    trigger = self.viper.Trigger([decons_call], pos, info)
                    forall = self.viper.Forall(args_decl, [trigger], eq, pos, info)
                    foralls.append(forall)
                body = self._conjoin(foralls, pos, info)
                yield self.viper.DomainAxiom(adt.fresh(adt.adt_prefix +
                                             'decons_over_cons_' + cons.name),
                                             body, pos, info, adt.adt_domain_name)

    def _create_adt_axiom_deconstructor_types(self, adt: PythonClass,
                                              adt_type: DomainType, pos: Position,
                                              info: Info, ctx) -> List[DomainAxiom]:
        for cons in adt.all_subclasses[1:]:
            arg_decl = self.viper.LocalVarDecl('_adt', adt_type, pos, info)
            arg_val = self.viper.LocalVar('_adt', adt_type, pos, info)
            foralls = []
            for arg_name, arg_field in cons.fields.items():
                if (isinstance(arg_field.type, PythonClass) and
                        (arg_field.type.name in PRIMITIVES or arg_field.type is adt)):
                    continue
                arg_type = self.translate_type(arg_field.type, ctx)
                decons_call = self.viper.DomainFuncApp(adt.fresh(adt.adt_prefix +
                                                                 cons.name + '_' + arg_name),
                                                       [arg_val], arg_type, pos,
                                                       info, adt.adt_domain_name)
                trigger = self.viper.Trigger([decons_call], pos, info)
                check = self.type_check(decons_call, arg_field.type, pos, ctx, False)
                forall = self.viper.Forall([arg_decl], [trigger], check, pos, info)
                foralls.append(forall)
            if not foralls:
                continue
            body = self._conjoin(foralls, pos, info)
            yield self.viper.DomainAxiom(adt.fresh(adt.adt_prefix +
                                                   'decons_types_' + cons.name),
                                         body, pos, info, adt.adt_domain_name)


    def _create_adt_axiom_constructors_over_deconstructors(self, adt: PythonClass,
                                      adt_type: DomainType, pos: Position,
                                      info: Info, ctx: Context) -> List[DomainAxiom]:
        """
        Create domain axiom representing the distribution of constructors over
        deconstructors.
        """
        adt_obj_use = self.viper.LocalVar('obj', adt_type, pos, info)
        adt_obj_decl = self.viper.LocalVarDecl('obj', adt_type, pos, info)
        for cons in adt.all_subclasses[1:]:
            if len(cons.fields.items()) > 0:
                args = self._get_adt_cons_params_use(cons, adt.name, adt_type, pos, info,
                                                     ctx)
                triggers, decons_calls = [], []
                is_cons_call = self.viper.DomainFuncApp(adt.fresh(adt.adt_prefix
                                                        + 'is_' + cons.name),
                                                        [adt_obj_use],
                                                        self.viper.Bool,
                                                        pos, info,
                                                        adt.adt_domain_name)
                for (arg_name, _), arg in zip(cons.fields.items(), args):
                    decons_call = self.viper.DomainFuncApp(adt.fresh(adt.adt_prefix
                                                           + cons.name + '_' + arg_name),
                                                           [adt_obj_use], arg.typ(), pos,
                                                           info, adt.adt_domain_name)
                    decons_calls.append(decons_call)
                    triggers.append(self.viper.Trigger([decons_call], pos, info))
                cons_call = self.viper.DomainFuncApp(adt.fresh(adt.adt_prefix + cons.name),
                                                     decons_calls, adt_type, pos, info,
                                                     adt.adt_domain_name)
                eq = self.viper.EqCmp(adt_obj_use, cons_call, pos, info)
                body = self.viper.Implies(is_cons_call, eq, pos, info)
                adt_obj_decl = self.viper.LocalVarDecl('obj', adt_type, pos, info)
                trigger = self.viper.Trigger([is_cons_call], pos, info)
                forall = self.viper.Forall([adt_obj_decl], [trigger], body, pos, info)
                yield self.viper.DomainAxiom(adt.fresh(adt.adt_prefix + 'cons_'
                                             + cons.name + '_over_decons'), forall,
                                             pos, info, adt.adt_domain_name)

    def _create_adt_axiom_associate_cons_type_with_const(self, adt: PythonClass,
                                      adt_type: DomainType, pos: Position,
                                      info: Info, ctx: Context) -> List[DomainAxiom]:
        """
        Create domain axiom associating each construtor type with a
        respective constant.
        """
        adt_obj_use = self.viper.LocalVar('obj', adt_type, pos, info)
        for cons in adt.all_subclasses[1:]:
            args = self._get_adt_cons_params_use(cons, adt.name, adt_type, pos, info, ctx)
            cons_call = self.viper.DomainFuncApp(adt.fresh(adt.adt_prefix +
                                                 cons.name), args, adt_type, pos,
                                                 info, adt.adt_domain_name)
            cons_type_call = self.viper.DomainFuncApp(adt.fresh(adt.adt_prefix +
                                                      'cons_type'), [cons_call],
                                                      self.viper.Int, pos, info,
                                                      adt.adt_domain_name)
            cons_const_call = self.viper.DomainFuncApp(adt.fresh(adt.adt_prefix
                                                       + cons.name + '_type'), [],
                                                       self.viper.Int, pos, info,
                                                       adt.adt_domain_name)
            eq = self.viper.EqCmp(cons_type_call, cons_const_call, pos, info)
            if len(cons.fields.items()) == 0:
                forall = eq
            else:
                args_decl = self._get_adt_cons_params_decl(cons, adt.name, adt_type, pos,
                                                           info, ctx)
                trigger = self.viper.Trigger([cons_call], pos, info)
                forall = self.viper.Forall(args_decl, [trigger], eq, pos, info)
            yield self.viper.DomainAxiom(adt.fresh(adt.adt_prefix +
                                         'associate_cons_type_function_with_' +
                                         cons.name + '_constant'), forall, pos,
                                         info, adt.adt_domain_name)

    def _create_adt_axiom_constrain_cons_type_with_const(self, adt: PythonClass,
                                                         adt_type: DomainType,
                                                         pos: Position,
                                                         info: Info
                                                         ) -> List[DomainAxiom]:
        """
        Create domain axiom constraining each construtor type to a
        respective constant.
        """
        adt_obj_use = self.viper.LocalVar('obj', adt_type, pos, info)
        adt_obj_decl = self.viper.LocalVarDecl('obj', adt_type, pos, info)
        eqs = []
        for cons in adt.all_subclasses[1:]:
            cons_type_call = self.viper.DomainFuncApp(adt.fresh(adt.adt_prefix
                                                      + 'cons_type'), [adt_obj_use],
                                                        self.viper.Int, pos, info,
                                                        adt.adt_domain_name)
            cons_const_call = self.viper.DomainFuncApp(adt.fresh(adt.adt_prefix +
                                                       cons.name + '_type'), [],
                                                        self.viper.Int, pos, info,
                                                        adt.adt_domain_name)
            eqs.append(self.viper.EqCmp(cons_type_call, cons_const_call, pos, info))
        body = self._disjoin(eqs, pos, info)
        trigger = self.viper.Trigger([cons_type_call], pos, info)
        forall = self.viper.Forall([adt_obj_decl], [trigger], body, pos, info)
        yield self.viper.DomainAxiom(adt.fresh(adt.adt_prefix +
                                     'constrain_cons_type_function_cons_constants'),
                                     forall, pos, info, adt.adt_domain_name)

    def _create_adt_axiom_associate_cons_type_with_bool(self, adt: PythonClass,
                                                        adt_type: DomainType,
                                                        pos: Position,
                                                        info: Info
                                                        ) -> List[DomainAxiom]:
        """
        Create domain axiom associating each construtor type to a
        boolean function that returns true when the ADT was created
        by the constructor the boolean function refers to.
        """
        adt_obj_use = self.viper.LocalVar('obj', adt_type, pos, info)
        adt_obj_decl = self.viper.LocalVarDecl('obj', adt_type, pos, info)
        for cons in adt.all_subclasses[1:]:
            cons_type_call = self.viper.DomainFuncApp(adt.fresh(adt.adt_prefix +
                                                      'cons_type'), [adt_obj_use],
                                                      self.viper.Int, pos, info,
                                                      adt.adt_domain_name)
            cons_const_call = self.viper.DomainFuncApp(adt.fresh(adt.adt_prefix +
                                                       cons.name + '_type'), [],
                                                       self.viper.Int, pos, info,
                                                       adt.adt_domain_name)
            type_id_eq = self.viper.EqCmp(cons_type_call, cons_const_call, pos, info)
            is_cons_call = self.viper.DomainFuncApp(adt.fresh(adt.adt_prefix + 'is_'
                                                    + cons.name), [adt_obj_use],
                                                    self.viper.Bool, pos, info,
                                                    adt.adt_domain_name)
            eqv = self.viper.EqCmp(type_id_eq, is_cons_call, pos, info)
            trigger = self.viper.Trigger([cons_type_call], pos, info)
            forall = self.viper.Forall([adt_obj_decl], [trigger], eqv, pos, info)
            yield self.viper.DomainAxiom(adt.fresh(adt.adt_prefix +
                                         'associate_cons_type_function_with_is_'
                                         + cons.name + '_bool_function'), forall,
                                         pos, info, adt.adt_domain_name)

    def _create_adt_axiom_cons_are_subclasses(self, adt: PythonClass,
                                              adt_type: DomainType, pos: Position,
                                              info: Info, ctx: Context
                                              ) -> List[DomainAxiom]:
        """
        Create domain axiom enforcing the fact that each constructor is a subclass
        of the class defining the ADT type. This axiom applies to PyType domain
        specifically.
        """
        ref_var_use = self.viper.LocalVar('ref', self.viper.Ref, pos, info)
        typeof_expr = self.type_factory.typeof(ref_var_use, ctx)
        func_call_expr = self.viper.DomainFuncApp(adt.sil_name, [],
                                                  self.type_factory.type_type(),
                                                  pos, info,
                                                  self.type_factory.type_domain)
        issubtype_expr = self.type_factory._issubtype(typeof_expr, func_call_expr,
                                                      ctx)
        eqs = []
        for cons in adt.all_subclasses[1:]:
            cons_call = self.viper.DomainFuncApp(cons.sil_name, [],
                                                 self.type_factory.type_type(),
                                                 pos, info,
                                                 self.type_factory.type_domain)
            eq = self.viper.EqCmp(typeof_expr, cons_call, pos, info)
            eqs.append(eq)
        or_expr = self._disjoin(eqs, pos, info)
        impl = self.viper.Implies(issubtype_expr, or_expr, pos, info)
        ref_var_decl = self.viper.LocalVarDecl('ref', self.viper.Ref, pos, info)
        trigger = self.viper.Trigger([issubtype_expr], pos, info)
        forall = self.viper.Forall([ref_var_decl], [trigger], impl, pos, info)
        yield self.viper.DomainAxiom(adt.fresh(adt.adt_prefix +
                                     'type_of_constructors'), forall, pos, info,
                                     adt.adt_domain_name)

    def _create_adt_func_box_and_unbox(self, adt: PythonClass, adt_type: DomainType,
                                       pos: Position, info: Info, ctx: Context
                                       ) -> List[Function]:
        """
        Create functions representing boxing and unboxing of the ADT to
        and from Ref, respectively.
        """
        ## Create box function
        adt_obj_use = self.viper.LocalVar('obj', adt_type, pos, info)
        adt_obj_decl = self.viper.LocalVarDecl('obj', adt_type, pos, info)
        adt_other_use = self.viper.LocalVar('___other', adt_type, pos, info)
        adt_other_decl = self.viper.LocalVarDecl('___other', adt_type, pos, info)
        postconds = []
        result = self.viper.Result(self.viper.Ref, pos, info)
        postconds.append(self.type_factory.type_check(result, adt, pos, ctx))
        unbox_func = self.viper.FuncApp(adt.fresh('unbox_' + adt.adt_domain_name),
                                        [result], pos, info, adt_type)
        postconds.append(self.viper.EqCmp(unbox_func, adt_obj_use, pos, info))
        box_func_name = adt.fresh('box_' + adt.adt_domain_name)
        for cons in adt.all_subclasses[1:]:
            is_cons_call = self.viper.DomainFuncApp(adt.fresh(adt.adt_prefix + 'is_'
                                                    + cons.name), [adt_obj_use],
                                                    self.viper.Bool, pos, info,
                                                    adt.adt_domain_name)
            typeof_call = self.type_factory.typeof(result, ctx)
            const_call = self.viper.DomainFuncApp(cons.sil_name, [],
                         self.type_factory.type_type(), pos, info,
                         self.type_factory.type_domain)
            typeof_eq = self.viper.EqCmp(typeof_call, const_call, pos, info)
            postconds.append(self.viper.Implies(is_cons_call, typeof_eq, pos, info))
            other_object = self.viper.FuncApp(box_func_name, [adt_other_use], pos, info,
                                              self.viper.Ref, [adt_other_decl])
            other_is_result = self.viper.EqCmp(self.viper.Result(self.viper.Ref, pos, info),
                                               other_object, pos, info)
            args_equal = self.viper.EqCmp(adt_obj_use, adt_other_use, pos, info)
            both_equal = self.viper.EqCmp(args_equal, other_is_result, pos, info)
            trigger = self.viper.Trigger([other_object], pos, info)
            quant = self.viper.Forall([adt_other_decl], [trigger], both_equal, pos, info)
            postconds.append(quant)
        yield self.viper.Function(box_func_name,
                                  [adt_obj_decl], self.viper.Ref, [], postconds,
                                  None, pos, info)

        ## Create unbox function
        preconds = []
        postconds = []
        adt_ref_use = self.viper.LocalVar('ref', self.viper.Ref, pos, info)
        preconds.append(self.type_factory.type_check(adt_ref_use, adt, pos, ctx))
        result = self.viper.Result(adt_type, pos, info)
        box_func = self.viper.FuncApp(adt.fresh('box_' + adt.adt_domain_name),
                                      [result], pos, info, self.viper.Ref)
        postconds.append(self.viper.EqCmp(box_func, adt_ref_use, pos, info))
        adt_ref_decl = self.viper.LocalVarDecl('ref', self.viper.Ref, pos, info)
        yield self.viper.Function(adt.fresh('unbox_' + adt.adt_domain_name),
                                  [adt_ref_decl], adt_type, preconds, postconds,
                                  None, pos, info)

    def create_adts_domains_and_functions(self, adts: List[PythonClass],
                                          ctx: Context) -> List['silver.ast.domain']:
        """
        Translate Algebraic Data Types defined in Python, with classes (sum)
        and a NamedTuple (product), to a domain in Viper. Further documentation
        on ADT syntax can be found in ADT.py.
        """

        info = self.no_info(ctx)
        domains = []
        functions = []

        for adt in adts:
            assert adt.is_adt and adt.is_defining_adt

            # ADTs should have constructors
            if not len(adt.all_subclasses) > 1:
                raise InvalidProgramException(adt.node, 'malformed.adt',
                    'malformed algebraic datatype: ADT has no constructors, ' +
                    'which should be defined as subclasses of the ADT class')

            # Create a domain type for each ADT and its constructors and
            # deconstructors
            adt_type = self.viper.DomainType(adt.adt_domain_name, {}, [])

            # All positions refer to ADT definition
            pos = self.to_position(adt, ctx)

            # Create domain functions
            domain_funcs = []

            ## Create constructors
            domain_funcs.extend(self._create_adt_func_constructors(adt,
                                adt_type, pos, info, ctx))

            ## Create deconstructors
            domain_funcs.extend(self._create_adt_func_deconstructors(adt,
                                adt_type, pos, info, ctx))
            
            ## Constructor types
            domain_funcs.extend(self._create_adt_func_constructor_types(adt,
                                adt_type, pos, info))

            # Create domain axioms
            axioms = []

            axioms.extend(self._create_adt_equality_axioms(adt, adt_type, pos, info, ctx))

            ## Destructors over constructors
            axioms.extend(self._create_adt_axiom_deconstructors_over_constructors(
                          adt, adt_type, pos, info, ctx))

            axioms.extend(self._create_adt_axiom_deconstructor_types(
                adt, adt_type, pos, info, ctx))

            ## Constructors over destructors
            axioms.extend(self._create_adt_axiom_constructors_over_deconstructors(
                          adt, adt_type, pos, info, ctx))

            ## Associate constructor type function with constructor constant
            axioms.extend(self._create_adt_axiom_associate_cons_type_with_const(
                          adt, adt_type, pos, info, ctx))

            ## Constrain constructor type function to constructor constants
            axioms.extend(self._create_adt_axiom_constrain_cons_type_with_const(
                          adt, adt_type, pos, info))

            ## Associate constructor type function with constructor boolean function
            axioms.extend(self._create_adt_axiom_associate_cons_type_with_bool(
                          adt, adt_type, pos, info))

            ## Express the fact that constructors can only be subclasses of the
            ## ADT (abstract class)
            axioms.extend(self._create_adt_axiom_cons_are_subclasses(
                          adt, adt_type, pos, info, ctx))

            # Create domain
            domains.append(self.viper.Domain(adt.adt_domain_name, domain_funcs,
                           axioms, [], pos, info))

            # Create ADT boxing and unboxing functions
            functions.extend(self._create_adt_func_box_and_unbox(adt, adt_type,
                             pos, info, ctx))

        return domains, functions

    def translate_program(self, modules: List[PythonModule], sil_progs: Program,
                          ctx: Context, selected: Set[str] = None,
                          ignore_global: bool = False) -> Program:
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
        predicates.extend(self.create_thread_predicates(ctx))
        functions.append(self.create_joinable_function(ctx))
        fields.extend(obl_fields)

        functions.extend(self.create_definedness_functions(ctx))
        functions.extend(self.create_asserting_function(ctx))
        functions.append(self.create_arbitrary_bool_func(ctx))
        predicates.append(self.create_may_set_predicate(ctx))

        type_funcs = self.type_factory.get_default_functions(ctx)
        type_axioms = self.type_factory.get_default_axioms(ctx)

        predicate_families = OrderedDict()
        static_fields = OrderedDict()
        func_constants = []

        threading_ids_constants = []
        # Silver names of the set of nodes which have been selected by the user
        # to be verified (if any).
        selected_names = []

        # List of classes that define algebraic data types
        adt_list = []

        all_names = []

        # First iteration over all modules: translate global variables, static
        # fields, and default arguments.
        for module in modules:
            ctx.module = module
            containers = [module]
            for class_name, cls in module.classes.items():
                if class_name in PRIMITIVES or class_name != cls.name:
                    # Skip primitives or entries for type variables.
                    continue
                if cls.is_adt:
                    # Prevents fields from being generated
                    continue
                if module is not module.global_module:
                    all_names.append(cls.sil_name)
                containers.append(cls)
                f_fields, f_funcs, f_methods = self._translate_fields(cls, all_names, ctx)
                fields += f_fields
                methods += f_methods
                functions += f_funcs
                ctx.current_class = cls
                for field_name in cls.all_static_fields:
                    field = cls.get_static_field(field_name)
                    current_field = field
                    while current_field.overrides:
                        current_field = current_field.overrides
                    static_fields.setdefault(current_field, []).append(cls)

            ctx.current_class = None
            # Translate default args
            for container in containers:
                for function in container.functions.values():
                    if module is not module.global_module:
                        all_names.append(function.sil_name)
                    self.track_dependencies(None, selected, function, ctx)
                    self.translate_default_args(function, ctx)
                for method in container.methods.values():
                    if module is not module.global_module:
                        all_names.append(method.sil_name)
                    self.track_dependencies(None, selected, method, ctx)
                    self.translate_default_args(method, ctx)
                for pred in container.predicates.values():
                    if module is not module.global_module:
                        all_names.append(pred.sil_name)
                    self.track_dependencies(None, selected, pred, ctx)
                    self.translate_default_args(pred, ctx)

        for root, classes in static_fields.items():
            self.track_dependencies(None, selected, root, ctx)
            functions.append(self.create_static_field_function(root, classes,
                                                               ctx))

        # Second iteration over all modules: Translate everything else.
        for module in modules:
            ctx.module = module

            for function in module.functions.values():
                if function.interface:
                    continue
                self.track_dependencies(selected_names, selected, function, ctx)
                functions.append(self.translate_function(function, ctx))
                func_constants.append(self.translate_function_constant(function, ctx))
            for method in module.methods.values():
                id_constant = self.translate_method_id_to_constant(method, ctx)
                threading_ids_constants.append(id_constant)
                if method.interface:
                    continue
                self.track_dependencies(selected_names, selected, method, ctx)
                methods.append(self.translate_method(method, ctx))
            for pred in module.predicates.values():
                self.track_dependencies(selected_names, selected, pred, ctx)
                predicates.append(self.translate_predicate(pred, ctx))
            for class_name, cls in module.classes.items():
                if class_name in PRIMITIVES or class_name != cls.name:
                    # Skip primitives and type variable entries.
                    continue
                if cls.is_adt and cls.is_defining_adt:
                    adt_list.append(cls)
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
                    self.track_dependencies(selected_names, selected, func, ctx)
                    functions.append(self.translate_function(func, ctx))
                    func_constants.append(self.translate_function_constant(func, ctx))
                    if func.overrides and not ((func_name in ('__str__', '__bool__') and
                                                func.overrides.cls.name == 'object') or
                                               (func_name in ('__getitem__',) and func.overrides.cls.name == 'dict')):
                        # We allow overriding certain methods, since the basic versions
                        # in object are already minimal.
                        raise InvalidProgramException(func.node,
                                                      'invalid.override')
                for method_name in cls.methods:
                    method = cls.methods[method_name]
                    threading_ids_constants.append(
                        self.translate_method_id_to_constant(method, ctx))
                    if method.interface:
                        continue
                    self.track_dependencies(selected_names, selected, method, ctx)
                    methods.append(self.translate_method(method, ctx))
                    if ((method_name != '__init__' or
                             (cls.superclass and
                              cls.superclass.python_class.has_classmethod)) and
                            method.overrides):
                        methods.append(self.create_override_check(method, ctx))
                for method_name in cls.static_methods:
                    method = cls.static_methods[method_name]
                    if module is not module.global_module:
                        all_names.append(method.sil_name)
                    threading_ids_constants.append(
                        self.translate_method_id_to_constant(method, ctx))
                    self.track_dependencies(selected_names, selected, method, ctx)
                    methods.append(self.translate_method(method, ctx))
                    if method.overrides:
                        methods.append(self.create_override_check(method, ctx))
                for method_name in cls.all_methods:
                    method = cls.get_method(method_name)
                    if (method.cls and method.cls != cls and
                            method_name != '__init__' and
                            method.method_type == MethodType.normal and
                            not method.interface and
                            not method.contract_only):
                        # Inherited
                        methods.append(self.create_inherit_check(method, cls,
                                                                 ctx))
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

        if not ignore_global:
            main_py_method, main_method = self.translate_main_method(modules, ctx)
            methods.append(main_method)
            self.track_dependencies(selected_names, selected, main_py_method, ctx)

        # Translate global variables.
        for module in modules:
            ctx.module = module
            for var in module.global_vars.values():
                if not var.module is module:
                    continue
                self.track_dependencies(selected_names, selected, var, ctx)
                # TODO: Check for every references function:
                # - if it doesnt exist yet it has no precondition so its okay
                # - if its precondition contains predicates or perms
                functions.append(
                    self.create_global_var_function(var, ctx))

        # IO operations are translated last because we need to know which functions are
        # used with Eval.
        for module in modules:
            for operation in module.io_operations.values():
                if module is not module.global_module:
                    all_names.append(operation.sil_name)
                self.track_dependencies(selected_names, selected, operation, ctx)
                predicate, getters, checkers = self.translate_io_operation(
                    operation,
                    ctx)
                predicates.append(predicate)
                functions.extend(getters)
                methods.extend(checkers)

        for root in predicate_families:
            self.track_dependencies(selected_names, selected, root, ctx)
            pf = self.translate_predicate_family(root, predicate_families[root],
                                                 ctx)
            predicates.append(pf)

        all_used_names = None

        if not selected:
            selected_names = all_names
            selected_names.extend(
                ['MustTerminate', 'MustInvokeBounded', 'MustInvokeUnbounded', 'Level', '_MaySet', 'main'])
            for cname in ['NoneType', 'object', 'Place', 'Thread', 'Exception', 'PSeq', 'PSet', 'tuple']:
                selected_names.append(module.global_module.classes[cname].sil_name)
            # Compute all dependencies of directly selected methods/...
        all_used_names = list(selected_names)
        i = 0
        while i < len(all_used_names):
            name = all_used_names[i]
            to_add = set()
            if name in self.viper.used_names_sets:
                to_add = self.viper.used_names_sets[name]
            if name in self.required_names:
                to_add = self.required_names[name]
            for add in to_add:
                if not add in all_used_names:
                    all_used_names.append(add)
            if name in modules[0].global_module.classes:
                superclass = modules[0].global_module.classes[name].superclass
                if superclass is not None:
                    all_used_names.append(superclass.sil_name)
            i += 1

        all_used_names = set(all_used_names)
        # Filter out anything the selected part does not depend on.
        predicates = [p for p in predicates if p.name() in all_used_names]
        functions = [f for f in functions if f.name() in all_used_names]
        methods = [m for m in methods if m.name() in all_used_names]

        ctx.current_function = None

        domains.append(self.type_factory.create_type_domain(type_funcs,
                                                            type_axioms, ctx))

        if ctx.are_function_constants_used:
            domains.append(self.create_functions_domain(func_constants, ctx))
        if ctx.are_threading_constants_used:
            domains.append(self.create_method_id_domain(threading_ids_constants, ctx))
            domains.append(self.create_thread_domain(ctx))
        adts_domains, adts_functions = self.create_adts_domains_and_functions(adt_list,
                                                                              ctx)
        domains.extend(adts_domains)
        functions.extend(adts_functions)

        converted_sil_progs = self._convert_silver_elements(sil_progs, all_used_names, not ignore_global, ctx)
        s_domains, s_predicates, s_functions, s_methods = converted_sil_progs
        domains += s_domains
        predicates += s_predicates
        functions += s_functions
        methods += s_methods

        prog = self.viper.Program(domains, fields, functions, predicates,
                                  methods, self.no_position(ctx),
                                  self.no_info(ctx))
        return prog

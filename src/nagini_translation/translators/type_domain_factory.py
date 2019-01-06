"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import ast

from nagini_translation.lib.constants import OBJECT_TYPE, PRIMITIVES, TUPLE_TYPE
from nagini_translation.lib.program_nodes import (
    GenericType,
    OptionalType,
    PythonClass,
    PythonType,
    TypeVar,
    UnionType,
)
from nagini_translation.lib.viper_ast import ViperAST
from nagini_translation.translators.abstract import Context, Expr
from typing import List, Tuple


class TypeDomainFactory:
    """
    Creates domain functions and axioms that represent the Python/mypy type
    system within Viper.
    """

    def __init__(self, viper: ViperAST, translator: 'Translator') -> None:
        self.viper = viper
        self.type_domain = 'PyType'
        self.translator = translator
        self.created_types = []
        self.union_type_size = 0

    def require_union_type_size(self, min_size: int) -> None:
        if self.union_type_size < min_size:
            self.union_type_size = min_size

    def no_position(self, ctx: Context) -> 'silver.ast.Position':
        return self.translator.no_position(ctx)

    def to_position(self, node: ast.AST, ctx: Context) -> 'silver.ast.Position':
        return self.translator.to_position(node, ctx)

    def no_info(self, ctx: Context) -> 'silver.ast.Position':
        return self.translator.no_info(ctx)

    def get_default_axioms(self,
                           ctx: Context) -> List['silver.ast.DomainAxiom']:
        result = [
            self.create_reflexivity_axiom(ctx),
            self.create_null_type_axiom(ctx),
            self.create_object_subtype_axiom(ctx),
        ]
        result.extend(self.create_union_subtype_axioms(ctx))
        return result

    def get_default_functions(self,
                              ctx: Context) -> List['silver.ast.DomainFunc']:
        result = [
            self.issubtype_func(ctx),
            self.typeof_func(ctx),
            self.tuple_args_func(ctx)
        ]
        result.extend(self.union_funcs(ctx))
        return result

    def union_funcs(self, ctx: Context) -> List['silver.ast.DomainFunc']:
        """
        Creates UNION_TYPE_SIZE functions of the following form:
        function union_type_n(arg_1: PyType, ..., arg_n: PyType): PyType
        """
        result = []
        position, info = self.no_position(ctx), self.no_info(ctx)
        args = []
        subt_arg = self.viper.LocalVarDecl('X', self.type_type(),
                                          position, info)
        for i in range(1, self.union_type_size + 1):
            arg = self.viper.LocalVarDecl('arg_' + str(i), self.type_type(),
                                          position, info)
            args.append(arg)
            func = self.viper.DomainFunc('union_type_' + str(i), args,
                                         self.type_type(), False, position,
                                         info, self.type_domain)
            result.append(func)
            func = self.viper.DomainFunc('issubtypeunion_type_' + str(i), [subt_arg] + args,
                                         self.viper.Bool, False, position,
                                         info, self.type_domain)
            result.append(func)
        return result

    def create_union_subtype_axioms(self,
            ctx: Context) -> List['silver.ast.DomainAxiom']:
        """
        Creates UNION_TYPE_SIZE axioms of the following form:
        (forall arg_1: PyType, ..., arg_n: PyType, X: PyType ::
        { issubtype(X, union_type_n(arg_1, ..., arg_n)) }
          issubtype(X, union_type_n(arg_1, ..., arg_n)) ==
          (false || issubtype(X, arg_1) || ... || issubtype(X, arg_n)))
        """
        result = []
        position, info = self.no_position(ctx), self.no_info(ctx)
        arg_decls = []
        args = []
        arg_subtype = self.viper.FalseLit(position, info)
        sub_decl = self.viper.LocalVarDecl('X', self.type_type(), position,
                                           info)
        sub_var = self.viper.LocalVar('X', self.type_type(), position, info)
        for i in range(1, self.union_type_size + 1):
            arg_decl = self.viper.LocalVarDecl('arg_' + str(i), self.type_type(),
                                                position, info)
            arg = self.viper.LocalVar('arg_' + str(i), self.type_type(), position,
                                      info)
            arg_decls.append(arg_decl)
            args.append(arg)
            union = self.viper.DomainFuncApp('union_type_' + str(i), args,
                                             self.type_type(), position,
                                             info, self.type_domain)
            subtype_union = self._issubtype(sub_var, union, ctx, position)
            subtype_union_general = self._issubtype(sub_var, union, ctx, position,
                                                    force_general=True)
            current_arg_subtype = self._issubtype(sub_var, arg, ctx, position)
            arg_subtype = self.viper.Or(arg_subtype, current_arg_subtype,
                                        position, info)
            body = self.viper.EqCmp(subtype_union, arg_subtype, position, info)
            trigger1 = self.viper.Trigger([subtype_union], position, info)
            forall1 = self.viper.Forall(arg_decls + [sub_decl], [trigger1], body,
                                       position, info)
            trigger2 = self.viper.Trigger([subtype_union_general], position, info)
            implication = self.viper.EqCmp(subtype_union_general, subtype_union,
                                             position, info)
            forall2 = self.viper.Forall(arg_decls + [sub_decl], [trigger2], implication,
                                        position, info)
            axiom_body = self.viper.And(forall1, forall2, position, info)
            axiom = self.viper.DomainAxiom('union_subtype_' + str(i), axiom_body,
                                           position, info, self.type_domain)
            result.append(axiom)
        return result

    def tuple_args_func(self, ctx: Context) -> 'silver.ast.DomainFunc':
        position, info = self.no_position(ctx), self.no_info(ctx)
        args = [self.viper.LocalVarDecl('t', self.type_type(), position, info)]
        result = self.viper.DomainFunc('tuple_args', args,
                                       self.viper.SeqType(self.type_type()),
                                       False, position, info, self.type_domain)
        return result

    def create_type(self, cls: 'PythonClass', used_names,
                    ctx: Context) -> Tuple['silver.ast.DomainFunc',
                                           'silver.ast.DomainAxiom']:
        """
        Creates the type domain function and subtype axiom for this class
        """
        if not cls.superclass:
            supertype = cls.module.global_module.classes[OBJECT_TYPE]
        else:
            supertype = cls.superclass
        position = self.to_position(cls.node, ctx)
        info = self.no_info(ctx)
        type_nargs = len(cls.type_vars) if cls.name != TUPLE_TYPE else -1
        type_funcs = self.create_type_function(cls.sil_name, type_nargs,
                                               position, info, ctx)
        if not cls.superclass and cls.name != OBJECT_TYPE:
            subtype_axioms = []
        else:
            subtype_axioms = []
            subtype_axioms.extend(self.create_self_subtype_axioms(cls, position, info, ctx, used_names))
            for other_type in self.created_types:
                subtype_axioms.append(self.create_subtype_axiom(cls, other_type, position, info, ctx))
            self.created_types.append(cls)
        funcs = type_funcs
        axioms = subtype_axioms
        if cls.type_vars or cls.name == TUPLE_TYPE:
            funcs.extend(self.create_arg_functions(cls, ctx))
            # create functions for type arguments
            axioms.extend(self.create_arg_axioms(cls, ctx))
            # create axioms that relate arguments to functions

        return funcs, axioms

    def create_arg_functions(self, cls: 'PythonClass',
                             ctx: Context) -> List['silver.ast.DomainFunc']:
        if cls.name == TUPLE_TYPE:
            return []
        position, info = self.no_position(ctx), self.no_info(ctx)
        result = []
        name = cls.sil_name + '_arg'
        args = []
        args.append(
            self.viper.LocalVarDecl('typ', self.type_type(), position, info))
        args.append(
            self.viper.LocalVarDecl('index', self.viper.Int, position, info))
        result = self.viper.DomainFunc(name, args, self.type_type(), False,
                                       position, info, self.type_domain)
        return [result]

    def create_arg_axioms(self, cls: 'PythonClass',
                          ctx: Context) -> List['silver.ast.DomainAxiom']:
        """
        Creates an axiom defining the type argument getter functions for a given
        type, e.g. for Sequence:
        (forall Z: PyType, arg0: PyType ::
          issubtype(Z, Sequence(arg0)) ==> Sequence_arg(Z, 0) == arg0)
        """
        position, info = self.no_position(ctx), self.no_info(ctx)
        z_decl = self.viper.LocalVarDecl('Z', self.type_type(), position, info)
        z_ref = self.viper.LocalVar('Z', self.type_type(), position, info)
        decls = [z_decl]
        type_args = []
        for i, var in enumerate(cls.type_vars):
            name = 'arg' + str(i)
            decl = self.viper.LocalVarDecl(name, self.type_type(), position,
                                           info)
            ref = self.viper.LocalVar(name, self.type_type(), position, info)
            decls.append(decl)
            type_args.append(ref)
        result = []
        func_lit = self.viper.DomainFuncApp(cls.sil_name, type_args,
                                            self.type_type(), position, info,
                                            self.type_domain)
        subtype = self._issubtype(z_ref, func_lit, ctx)
        subtype_general = self._issubtype(z_ref, func_lit, ctx, force_general=True)
        if cls.name == TUPLE_TYPE:
            return []
            # args = [z_ref]
            # decls = [z_decl]
            # type_seq = self.viper.SeqType(self.type_type())
            # name = 'args'
            # decl = self.viper.LocalVarDecl(name, type_seq, position,
            #                                info)
            # ref = self.viper.LocalVar(name, type_seq, position, info)
            # decls.append(decl)
            # type_args = ref
            # func_lit = self.viper.DomainFuncApp(cls.sil_name, [type_args],
            #                                     self.type_type(), position, info,
            #                                     self.type_domain)
            # subtype = self._issubtype(z_ref, func_lit, ctx)
            #
            # current_arg = self.viper.DomainFuncApp(cls.sil_name + '_args', args,
            #                                        type_seq, position,
            #                                        info, self.type_domain)
            # rhs = self.viper.EqCmp(current_arg, type_args, position,
            #                        info)
            # implication = self.viper.Implies(subtype, rhs, position, info)
            # trigger1 = self.viper.Trigger([subtype], position, info)
            # quantifier = self.viper.Forall(decls, [trigger1], implication,
            #                                position, info)
            # axiom = self.viper.DomainAxiom(cls.sil_name + '_args_seq',
            #                                quantifier, position, info,
            #                                self.type_domain)
            # return [axiom]
        for i, var in enumerate(cls.type_vars):
            args = [z_ref, self.viper.IntLit(i, position, info)]
            current_arg = self.viper.DomainFuncApp(cls.sil_name + '_arg', args,
                                                   self.type_type(), position,
                                                   info, self.type_domain)
            rhs = self.viper.EqCmp(current_arg, type_args[i], position,
                                       info)
            implication = self.viper.Implies(subtype, rhs, position, info)
            trigger1 = self.viper.Trigger([subtype], position, info)
            # trigger2 = self.viper.Trigger([current_arg, subtype_general], position, info)
            quantifier = self.viper.Forall(decls, [trigger1], implication,
                                           position, info)
            axiom = self.viper.DomainAxiom(cls.sil_name + '_args' + str(i),
                                           quantifier, position, info,
                                           self.type_domain)
            result.append(axiom)
        return result

    def create_type_function(self, name: str, type_nargs: int,
                             position: 'silver.ast.Position',
                             info: 'silver.ast.Info',
                             ctx: Context) -> List['silver.ast.DomainFunc']:
        args = []
        result = []
        # if type_nargs != 0:
        #     result.append(self.viper.DomainFunc(name + '_basic', [], self.type_type(),
        #                                         True, position, info, self.type_domain))
        if type_nargs == -1:
            seq_type = self.viper.SeqType(self.type_type())
            args.append(self.viper.LocalVarDecl('args', seq_type, position,
                                                info))
        else:
            for i in range(type_nargs):
                args.append(self.viper.LocalVarDecl('arg' + str(i),
                                                    self.type_type(), position,
                                                    info))
        result.append(self.viper.DomainFunc(name, args, self.type_type(),
                                            len(args) == 0, position, info,
                                            self.type_domain))
        t_arg = self.viper.LocalVarDecl('___t', self.type_type(), position, info)
        result.append(self.viper.DomainFunc('issubtype' + name, [t_arg] + args, self.viper.Bool, False, position, info, self.type_domain))
        return result

    def create_type_domain(self, type_funcs: List['silver.ast.DomainFunc'],
                           type_axioms: List['silver.ast.DomainAxiom'],
                           ctx: Context) -> 'silver.ast.Domain':
        result = self.viper.Domain(self.type_domain, type_funcs, type_axioms,
                                   [], self.no_position(ctx), self.no_info(ctx))
        return result

    def type_type(self) -> 'silver.ast.DomainType':
        """
        Creates a reference to the domain type we use for the Python types
        """
        return self.viper.DomainType(self.type_domain, {}, [])

    def _issubtype(self, sub: Expr, super: Expr, ctx: Context,
                   position=None, force_general=False) -> 'silver.ast.DomainFuncApp':
        if not position:
            position = self.no_position(ctx)
        if force_general or not isinstance(super, self.viper.ast.DomainFuncApp) or super.funcname().endswith('_arg') or super.funcname() == 'typeof':
            return self.viper.DomainFuncApp('issubtype', [sub, super],
                                            self.viper.Bool, position,
                                            self.no_info(ctx), self.type_domain)
        else:
            assert isinstance(super, self.viper.ast.DomainFuncApp)
            args = self.viper.to_list(super.args())
            return self.viper.DomainFuncApp('issubtype' + super.funcname(), [sub] + args,
                                            self.viper.Bool, position,
                                            self.no_info(ctx), self.type_domain)

    def _issubtype_app(self, name: str, sub: Expr, super: Expr, ctx: Context,
                       position=None) -> 'silver.ast.DomainFuncApp':
        if not position:
            position = self.no_position(ctx)
        return self.viper.DomainFuncApp(name, [sub, super],
                                        self.viper.Bool, position,
                                        self.no_info(ctx), self.type_domain)

    def typeof(self, arg: Expr, ctx: Context) -> 'silver.ast.DomainFuncApp':
        return self.viper.DomainFuncApp('typeof', [arg], self.type_type(),
                                        self.no_position(ctx),
                                        self.no_info(ctx),
                                        self.type_domain)

    def create_self_subtype_axioms(self, type: PythonType,
                             position: 'silver.ast.Position',
                             info: 'silver.ast.Info',
                             ctx: Context, used_names) -> 'silver.ast.DomainAxiom':
        type_arg_decls = []
        type_args = []
        if type.name == TUPLE_TYPE:
            seq_type = self.viper.SeqType(self.type_type())
            args_ref = self.viper.LocalVar('args', seq_type, position, info)
            type_args.append(args_ref)
            type_arg_decls.append(
                self.viper.LocalVarDecl('args', seq_type, position, info))
        else:
            for name, var in type.type_vars.items():
                var = self.viper.LocalVar(name, self.type_type(), position,
                                          info)
                type_args.append(var)
                type_arg_decls.append(self.viper.LocalVarDecl(name,
                                                              self.type_type(),
                                                              position, info))
                ctx.bound_type_vars[(type.name, name)] = var

        type_var = self.viper.LocalVar('class', self.type_type(), position,
                                       info)
        type_func = self.viper.DomainFuncApp(type.sil_name, type_args,
                                             self.type_type(), position, info,
                                             self.type_domain)
        body = self._issubtype(type_func, type_func, ctx, position)
        if type.name == TUPLE_TYPE:
            tuple_args = self.viper.DomainFuncApp('tuple_args', [type_func], seq_type,
                                                  position, info, self.type_domain)
            args_def = self.viper.EqCmp(tuple_args, args_ref, position, info)
            body = self.viper.And(body, args_def, position, info)
        if type_arg_decls:
            trigger =self.viper.Trigger([type_func], position, info)
            body = self.viper.Forall(type_arg_decls, [trigger], body, position, info)

        for subclass in type.direct_subclasses:
            if subclass.name in PRIMITIVES or (used_names is not None and subclass.sil_name not in used_names):
                continue
            subclass_arg_decls = []
            subclass_args = []
            bound_subclass_vars = {}
            if subclass.name == TUPLE_TYPE:
                seq_subclass = self.viper.SeqType(self.type_type())
                args_ref = self.viper.LocalVar('args', seq_subclass, position, info)
                subclass_args.append(args_ref)
                subclass_arg_decls.append(
                    self.viper.LocalVarDecl('args', seq_subclass, position, info))
            else:
                for name, var in subclass.type_vars.items():
                    comp_name = subclass.name + '_' + var.name
                    var_ref = self.viper.LocalVar(comp_name, self.type_type(), position,
                                              info)
                    subclass_args.append(var_ref)
                    subclass_arg_decls.append(self.viper.LocalVarDecl(comp_name,
                                                                  self.type_type(),
                                                                  position, info))
                    bound_subclass_vars[(subclass.name, name)] = var_ref

            subclass_var = self.viper.LocalVar('class', self.type_type(), position,
                                           info)
            subclass_func = self.viper.DomainFuncApp(subclass.sil_name, subclass_args,
                                                 self.type_type(), position, info,
                                                 self.type_domain)
            subclass_expr = self._issubtype(type_func, subclass_func, ctx, position)
            subclass_body = self.viper.Not(subclass_expr, position, info)
            if type_arg_decls or subclass_arg_decls:
                subclass_trigger = self.viper.Trigger([subclass_expr], position, info)
                subclass_body = self.viper.Forall(type_arg_decls + subclass_arg_decls, [subclass_trigger], subclass_body, position, info)
            body = self.viper.And(body, subclass_body, position, info)

        res= [self.viper.DomainAxiom('___selfsub' + type.sil_name, body, position, info, self.type_domain)]

        t_decl = self.viper.LocalVarDecl('_______t', self.type_type(), position, info)
        t = self.viper.LocalVar('_______t', self.type_type(), position, info)
        one_part = self._issubtype(t, type_func, ctx, position)
        other_part = self._issubtype_app('issubtype', t, type_func, ctx, position)
        other_body = self.viper.EqCmp(one_part, other_part, position, info)
        if type.name == TUPLE_TYPE:
            trigger1 = self.viper.Trigger([one_part], position, info)
            trigger2 = self.viper.Trigger([other_part], position, info)
            triggers = [trigger1, trigger2]
            tuple_args = self.viper.DomainFuncApp('tuple_args', [t], seq_type,
                                                  position, info, self.type_domain)
            j_decl = self.viper.LocalVarDecl('___j', self.viper.Int, position, info)
            j_ref = self.viper.LocalVar('___j', self.viper.Int, position, info)
            tuple_arg_j = self.viper.SeqIndex(tuple_args, j_ref, position, info)
            arg_j = self.viper.SeqIndex(args_ref, j_ref, position, info)
            zero = self.viper.IntLit(0, position, info)
            j_positive = self.viper.GeCmp(j_ref, zero, position, info)
            tuple_args_len = self.viper.SeqLength(tuple_args, position, info)
            args_len = self.viper.SeqLength(args_ref, position, info)
            j_lt_args = self.viper.LtCmp(j_ref, tuple_args_len, position, info)
            j_in_range = self.viper.And(j_positive, j_lt_args, position, info)
            j_subtype = self._issubtype(tuple_arg_j, arg_j, ctx, position)
            inner_implication = self.viper.Implies(j_in_range, j_subtype, position, info)
            inner_trigger = self.viper.Trigger([tuple_arg_j], position, info)
            inner_forall = self.viper.Forall([j_decl], [inner_trigger], inner_implication, position, info)
            some_tuple = self.viper.DomainFuncApp(type.sil_name, [tuple_args], self.type_type(), position, info, self.type_domain)
            is_some_tuple = self._issubtype(t, some_tuple, ctx, position)
            inner_forall = self.viper.And(is_some_tuple, inner_forall, position, info)
            len_eq = self.viper.EqCmp(tuple_args_len, args_len, position, info)
            inner_forall = self.viper.And(len_eq, inner_forall, position, info)
            forall_def = self.viper.EqCmp(one_part, inner_forall, position, info)
            other_body = self.viper.And(other_body, forall_def, position, info)
        else:
            trigger = self.viper.Trigger([other_part], position, info)
            triggers = [trigger]
        body = self.viper.Forall([t_decl] + type_arg_decls, triggers, other_body, position, info)

        if isinstance(type.superclass, GenericType):
            supertype_instance = self.subtype_check(t, type.superclass, position, ctx,
                                                    False)
            new_body = self.viper.Implies(one_part, supertype_instance, position, info)
            new_forall = self.viper.Forall([t_decl] + type_arg_decls, [self.viper.Trigger([one_part], position, info)], new_body, position, info)
            body = self.viper.And(body, new_forall, position, info)

        res.append(self.viper.DomainAxiom('___issubtype_' + type.sil_name, body, position, info, self.type_domain))
        for name, var in type.type_vars.items():
            del ctx.bound_type_vars[(type.name, name)]
        return res

    def create_subtype_axiom(self, type: PythonType, other_type: PythonType,
                             position: 'silver.ast.Position',
                             info: 'silver.ast.Info',
                             ctx: Context) -> 'silver.ast.DomainAxiom':
        type_arg_decls = []
        type_args = []
        bound_type_vars = {}
        if type.name == TUPLE_TYPE:
            seq_type = self.viper.SeqType(self.type_type())
            args_ref = self.viper.LocalVar('args', seq_type, position, info)
            type_args.append(args_ref)
            type_arg_decls.append(
                self.viper.LocalVarDecl('args', seq_type, position, info))
        else:
            for name, var in type.type_vars.items():
                var = self.viper.LocalVar(name, self.type_type(), position,
                                          info)
                type_args.append(var)
                type_arg_decls.append(self.viper.LocalVarDecl(name,
                                                              self.type_type(),
                                                              position, info))
                bound_type_vars[(type.name, name)] = var

        type_var = self.viper.LocalVar('class', self.type_type(), position,
                                       info)
        type_func = self.viper.DomainFuncApp(type.sil_name, type_args,
                                             self.type_type(), position, info,
                                             self.type_domain)

        other_type_arg_decls = []
        other_type_args = []
        other_bound_type_vars = {}
        if other_type.name == TUPLE_TYPE:
            seq_type = self.viper.SeqType(self.type_type())
            args_ref = self.viper.LocalVar('args', seq_type, position, info)
            other_type_args.append(args_ref)
            other_type_arg_decls.append(
                self.viper.LocalVarDecl('args', seq_type, position, info))
        else:
            for name, var in other_type.type_vars.items():
                var = self.viper.LocalVar('_'+name, self.type_type(), position,
                                          info)
                other_type_args.append(var)
                other_type_arg_decls.append(self.viper.LocalVarDecl('_'+name,
                                                              self.type_type(),
                                                              position, info))
                other_bound_type_vars[(other_type.name, name)] = var

        other_type_var = self.viper.LocalVar('oclass', self.type_type(), position,
                                       info)
        other_type_func = self.viper.DomainFuncApp(other_type.sil_name, other_type_args,
                                             self.type_type(), position, info,
                                             self.type_domain)

        common = type.python_class.get_common_superclass(other_type.python_class)
        t_decl = self.viper.LocalVarDecl('t', self.type_type(), position, info)
        t_ref = self.viper.LocalVar('t', self.type_type(), position, info)
        one = self._issubtype(t_ref, type_func, ctx, position)
        other = self._issubtype(t_ref, other_type_func, ctx, position)
        trigger = self.viper.Trigger([one, other], position, info)
        if common is type.python_class:
            fits = self.viper.TrueLit(position, info)
            other_and_fits = self.viper.And(other, fits, position, info)
            implication = self.viper.Implies(other_and_fits, one, position, info)
            body = self.viper.Forall([t_decl] + type_arg_decls + other_type_arg_decls,
                                     [trigger], implication, position, info)
            one_subtype_of_other = self._issubtype(type_func, other_type_func, ctx, position)
            one_not_subtype_of_other = self.viper.Not(one_subtype_of_other, position, info)
            if (type_arg_decls + other_type_arg_decls):
                trigger = self.viper.Trigger([one_subtype_of_other], position, info)
                one_not_subtype_of_other = self.viper.Forall(type_arg_decls + other_type_arg_decls, [trigger], one_not_subtype_of_other, position, info)
            body = self.viper.And(body, one_not_subtype_of_other, position, info)

        elif common is other_type.python_class:
            fits = self.viper.TrueLit(position, info)
            one_and_fits = self.viper.And(one, fits, position, info)
            implication = self.viper.Implies(one_and_fits, other, position, info)
            body = self.viper.Forall([t_decl] + type_arg_decls + other_type_arg_decls,
                                     [trigger], implication, position, info)
            one_subtype_of_other = self._issubtype(other_type_func, type_func, ctx,
                                                   position)
            one_not_subtype_of_other = self.viper.Not(one_subtype_of_other, position,
                                                      info)
            if (type_arg_decls + other_type_arg_decls):
                trigger = self.viper.Trigger([one_subtype_of_other], position, info)
                one_not_subtype_of_other = self.viper.Forall(
                    type_arg_decls + other_type_arg_decls, [trigger],
                    one_not_subtype_of_other, position, info)
            body = self.viper.And(body, one_not_subtype_of_other, position, info)

        else:
            not_one = self.viper.Not(one, position, info)
            not_other = self.viper.Not(other, position, info)
            either = self.viper.Or(not_one, not_other, position, info)
            body = self.viper.Forall([t_decl] + type_arg_decls + other_type_arg_decls, [trigger], either, position, info)
        return self.viper.DomainAxiom('___subtype_' + type.sil_name + '_' + other_type.sil_name, body, position, info, self.type_domain)

    def create_null_type_axiom(self, ctx: Context) -> 'silver.ast.DomainAxiom':
        """
        Creates an axiom that states that the type of null is None:

        forall r: Ref :: { typeof(r) }
          issubtype(typeof(r), NoneType()) == (r == null)
        """
        position, info = self.no_position(ctx), self.no_info(ctx)
        arg_r = self.viper.LocalVarDecl('r', self.viper.Ref, position, info)
        var_r = self.viper.LocalVar('r', self.viper.Ref, position, info)
        none_type = self.viper.DomainFuncApp('NoneType', [], self.type_type(),
                                             position, info, self.type_domain)
        t_decl = self.viper.LocalVarDecl('___t', self.type_type(), position, info)
        t_ref = self.viper.LocalVar('___t', self.type_type(), position, info)
        null = self.viper.NullLit(position, info)
        typeof_null = self.typeof(null, ctx)
        null_has_type_none = self._issubtype(typeof_null, none_type, ctx)

        subtype = self._issubtype(t_ref, none_type, ctx)
        subtype_general = self._issubtype(t_ref, none_type, ctx, force_general=True)

        biimplication = self.viper.EqCmp(subtype, subtype_general, position, info)
        trigger = self.viper.Trigger([subtype_general], position, info)
        quantifier = self.viper.Forall([t_decl], [trigger],
                                       biimplication, position, info)
        body = self.viper.And(null_has_type_none, quantifier, position, info)
        return self.viper.DomainAxiom('null_nonetype', body, position, info,
                                      self.type_domain)

    def create_reflexivity_axiom(self,
                                 ctx: Context) -> 'silver.ast.DomainAxiom':
        """
        Creates the reflexivity axiom for the PyType domain:
        forall type: PyType :: { issubtype(type, type) } issubtype(type, type)
        """
        position, info = self.no_position(ctx), self.no_info(ctx)
        arg = self.viper.LocalVarDecl('type_', self.type_type(), position, info)
        var = self.viper.LocalVar('type_', self.type_type(), position, info)
        reflexive_subtype = self._issubtype(var, var, ctx)
        trigger_exp = reflexive_subtype
        trigger = self.viper.Trigger([trigger_exp], position, info)
        body = self.viper.Forall([arg], [trigger], reflexive_subtype,
                                 position, info)
        return self.viper.DomainAxiom('issubtype_reflexivity', body,
                                      position, info, self.type_domain)

    def create_object_subtype_axiom(self,
                                    ctx: Context) -> 'silver.ast.DomainAxiom':
        """
        Creates the axiom saying that all types are subtypes of object:
        forall type: PyType :: { issubtype(type, object()) }
        issubtype(type, object())
        """
        position, info = self.no_position(ctx), self.no_info(ctx)
        arg = self.viper.LocalVarDecl('type_', self.type_type(), position, info)
        var = self.viper.LocalVar('type_', self.type_type(), position, info)
        object_type = self.viper.DomainFuncApp('object', [], self.type_type(),
                                               position, info, self.type_domain)
        object_subtype = self._issubtype(var, object_type, ctx)
        trigger_exp = object_subtype
        trigger = self.viper.Trigger([trigger_exp], position, info)
        body = self.viper.Forall([arg], [trigger], object_subtype, position,
                                 info)
        return self.viper.DomainAxiom('issubtype_object', body, position, info,
                                      self.type_domain)

    def typeof_func(self, ctx: Context) -> 'silver.ast.DomainFunc':
        """
        Creates the typeof domain function
        """
        obj_var = self.viper.LocalVarDecl('obj', self.viper.Ref,
                                          self.no_position(ctx),
                                          self.no_info(ctx))
        return self.viper.DomainFunc('typeof', [obj_var],
                                     self.type_type(), False,
                                     self.no_position(ctx), self.no_info(ctx),
                                     self.type_domain)

    def subtype_func(self, name: str, ctx: Context) -> 'silver.ast.DomainFunc':
        """
        Creates the issubtype, extends and isnotsubtype domain functions.
        """
        sub_var = self.viper.LocalVarDecl('sub', self.type_type(),
                                          self.no_position(ctx),
                                          self.no_info(ctx))
        super_var = self.viper.LocalVarDecl('super', self.type_type(),
                                            self.no_position(ctx),
                                            self.no_info(ctx))
        return self.viper.DomainFunc(name, [sub_var, super_var],
                                     self.viper.Bool, False,
                                     self.no_position(ctx), self.no_info(ctx),
                                     self.type_domain)

    def issubtype_func(self, ctx: Context) -> 'silver.ast.DomainFunc':
        return self.subtype_func('issubtype', ctx)

    def dynamic_type_check(self, lhs: 'Expr',
                           type: 'Expr', position: 'silver.ast.Position',
                           ctx: Context):
        type_func = self.typeof(lhs, ctx)
        result = self.viper.EqCmp(type_func, type, self.no_position(ctx),
                                  self.no_info(ctx))
        return result

    def subtype_check(self, type_func: 'Expr', type: 'PythonType',
                      position: 'silver.ast.Position',
                      ctx: Context, concrete: bool = False) -> Expr:
        """
        Creates an expression which denotes if the given ``type_func``
        expression is a subtype of (or, if ``concrete`` is true, equivalent to)
        the given ``type``.
        """
        info = self.no_info(ctx)
        if type.name == TUPLE_TYPE and isinstance(type, GenericType) and not type.exact_length:
            seq_type = self.viper.SeqType(self.type_type())
            tuple_args = self.viper.DomainFuncApp('tuple_args', [type_func],
                                                  seq_type, position, info,
                                                  self.type_domain)
            tuple_type = self.viper.DomainFuncApp(type.sil_name, [tuple_args],
                                                  self.type_type(), position, info,
                                                  self.type_domain)
            tuple_args_len = self.viper.SeqLength(tuple_args, position, info)
            basic = self._issubtype(type_func, tuple_type, ctx)
            if not type.exact_length:
                # issubtypetuple(type_func,tuple_args(type_func)) && forall i :: 0 <= i < |tuple_args(type_func)| ==> issubtype(tuple_args()[i], T)

                i_ref = self.viper.LocalVar('i', self.viper.Int, position, info)
                i_decl = self.viper.LocalVarDecl('i', self.viper.Int, position,
                                                 info)
                zero = self.viper.IntLit(0, position, info)
                i_ge_zero = self.viper.GeCmp(i_ref, zero, position, info)


                i_lt_len = self.viper.LtCmp(i_ref, tuple_args_len, position, info)
                i_in_bounds = self.viper.And(i_ge_zero, i_lt_len, position, info)

                tuple_arg = self.viper.SeqIndex(tuple_args, i_ref, position, info)
                arg_lit = self.translate_type_literal(type.type_args[0], position,
                                                      ctx)
                if concrete:
                    subtype = self.viper.EqCmp(tuple_arg, arg_lit, position, info)
                else:
                    subtype = self._issubtype(tuple_arg, arg_lit, ctx)
                implication = self.viper.Implies(i_in_bounds, subtype, position,
                                                 info)
                trigger = self.viper.Trigger([tuple_arg], position, info)
                forall = self.viper.Forall([i_decl], [trigger], implication,
                                           position, info)

                return self.viper.And(basic, forall, position, info)
            # issubtypetuple(type_func,tuple_args(type_func)) && |tuple_args| == bla && bigwedge
            len_lit = self.viper.IntLit(len(type.type_args), position, info)
            set_len = self.viper.EqCmp(tuple_args_len, len_lit, position, info)
            result = self.viper.And(basic, set_len, position, info)
            for i, arg in enumerate(type.type_args):
                i_lit = self.viper.IntLit(i, position, info)
                tuple_arg = self.viper.SeqIndex(tuple_args, i_lit, position, info)
                arg_subtype = self.subtype_check(tuple_arg, arg, position, ctx)
                result = self.viper.And(result, arg_subtype, position, info)
            return result

        supertype_func = self.translate_type_literal(type, position, ctx,
                                                     alias=type_func)

        var_sub = self.viper.LocalVar('sub', self.type_type(),
                                      self.no_position(ctx), self.no_info(ctx))
        var_super = self.viper.LocalVar('super', self.type_type(),
                                        self.no_position(ctx),
                                        self.no_info(ctx))
        if concrete:
            result = self.viper.EqCmp(type_func, supertype_func, position, info)
        else:
            result = self._issubtype(type_func, supertype_func, ctx,
                                     position=position)
            if isinstance(type, TypeVar):
                bound_result = self.subtype_check(type_func, type.bound, position, ctx,
                                                  False)
                result = self.viper.And(result, bound_result, position, info)
        return result

    def type_check(self, lhs: 'Expr', type: 'PythonType',
                   position: 'silver.ast.Position',
                   ctx: Context, concrete: bool = False) -> Expr:
        """
        Creates an expression checking if the type of the expression ``lhs``
        is a subtype of (or, if ``concrete`` is true, equivalent to) the given
        ``type``.
        """
        info = self.no_info(ctx)
        type_func = self.typeof(lhs, ctx)
        if isinstance(type, OptionalType):
            # Shortcut for performance reasons: Instead of using a real union type,
            # we say that lhs is None or it has the given type.
            none_part = self.viper.EqCmp(lhs, self.viper.NullLit(position, info),
                                         position, info)
            just_part = self.subtype_check(type_func, type.cls, position, ctx,
                                           concrete=concrete)
            return self.viper.Or(none_part, just_part, position, info)
        return self.subtype_check(type_func, type, position, ctx,
                                  concrete=concrete)

    def translate_type_literal(self, type: 'PythonType', position: 'Position',
                               ctx: Context, alias: Expr = None) -> Expr:
        """
        Translates the given type to a type literal. If the given type is
        a generic type with missing type argument information, the type
        arguments will be taken from the ``alias`` expression (which typically
        would be some expression known to be equivalent to the type being
        described).
        """
        info = self.no_info(ctx)
        if isinstance(type, TypeVar):
            if type.target_type:
                # Type parameter belongs to generic class.
                key = (type.target_type.name, type.name)
            else:
                # Type parameter belongs to generic method.
                key = (type.name,)
            return ctx.bound_type_vars[key]
        if type is None:
            type = ctx.module.global_module.classes['NoneType']
        args = []
        if isinstance(type, GenericType):
            for arg in type.type_args:
                args.append(self.translate_type_literal(arg, position, ctx))
            if not isinstance(type, UnionType):
                type = type.cls
        elif isinstance(type, PythonClass) and type.type_vars:
            assert alias
            for index, arg in enumerate(type.type_vars):
                args.append(self.get_type_arg(alias, type, index, ctx))
        if type.name == TUPLE_TYPE:
            if args:
                seq_arg = self.viper.ExplicitSeq(args, position, info)
            else:
                seq_arg = self.viper.EmptySeq(self.type_type(), position, info)
            args = [seq_arg]
        if type.name == 'Union':
            type_func_name = 'union_type_' + str(len(args))
            self.require_union_type_size(len(args))
        else:
            type_func_name = type.sil_name
        type_func = self.viper.DomainFuncApp(type_func_name, args,
                                             self.type_type(), position,
                                             info, self.type_domain)
        return type_func

    def get_type_arg(self, type_expr: Expr, target_type: PythonType,
                     index: int, ctx: Context) -> Expr:
        """
        Returns an expression denoting the type argument of the given type
        expression ``type_expr`` relative to the given ``target_type`` with
        the index ``index``.
        """
        arg_func_name = target_type.sil_name + '_arg'
        index_lit = self.viper.IntLit(index, self.no_position(ctx),
                                      self.no_info(ctx))
        args = [type_expr, index_lit]
        result = self.viper.DomainFuncApp(arg_func_name, args, self.type_type(),
                                          self.no_position(ctx),
                                          self.no_info(ctx),
                                          self.type_domain)
        return result

    def get_ref_type_arg(self, target_expr: Expr, target_type: PythonType,
                         index: int, ctx: Context):
        typeof = self.typeof(target_expr, ctx)
        return self.get_type_arg(typeof, target_type, index, ctx)

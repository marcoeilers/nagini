"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import ast

from nagini_translation.lib.constants import OBJECT_TYPE, TUPLE_TYPE
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
    UNION_TYPE_SIZE = 4

    def __init__(self, viper: ViperAST, translator: 'Translator') -> None:
        self.viper = viper
        self.type_domain = 'PyType'
        self.translator = translator

    def no_position(self, ctx: Context) -> 'silver.ast.Position':
        return self.translator.no_position(ctx)

    def to_position(self, node: ast.AST, ctx: Context) -> 'silver.ast.Position':
        return self.translator.to_position(node, ctx)

    def no_info(self, ctx: Context) -> 'silver.ast.Position':
        return self.translator.no_info(ctx)

    def get_default_axioms(self,
                           ctx: Context) -> List['silver.ast.DomainAxiom']:
        result = [
            self.create_transitivity_axiom(ctx),
            self.create_reflexivity_axiom(ctx),
            self.create_extends_implies_subtype_axiom(ctx),
            self.create_null_type_axiom(ctx),
            self.create_object_subtype_axiom(ctx),
            self.create_subtype_exclusion_axiom(ctx),
            self.create_subtype_exclusion_axiom_2(ctx),
            self.create_subtype_exclusion_propagation_axiom(ctx),
            self.create_tuple_arg_axiom(ctx),
            self.create_tuple_args_axiom(ctx),
            self.create_tuple_subtype_axiom(ctx),
        ]
        result.extend(self.create_union_subtype_axioms(ctx))
        result.extend(self.create_subtype_union_axioms(ctx))
        return result

    def get_default_functions(self,
                              ctx: Context) -> List['silver.ast.DomainFunc']:
        result = [
            self.extends_func(ctx),
            self.issubtype_func(ctx),
            self.isnotsubtype_func(ctx),
            self.tuple_args_func(ctx),
            self.typeof_func(ctx),
            self.basic_func(ctx),
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
        for i in range(1, self.UNION_TYPE_SIZE + 1):
            arg = self.viper.LocalVarDecl('arg_' + str(i), self.type_type(),
                                          position, info)
            args.append(arg)
            func = self.viper.DomainFunc('union_type_' + str(i), args,
                                         self.type_type(), False, position,
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
        for i in range(1, self.UNION_TYPE_SIZE + 1):
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
            current_arg_subtype = self._issubtype(sub_var, arg, ctx, position)
            arg_subtype = self.viper.Or(arg_subtype, current_arg_subtype,
                                        position, info)
            body = self.viper.EqCmp(subtype_union, arg_subtype, position, info)
            trigger = self.viper.Trigger([subtype_union], position, info)
            forall = self.viper.Forall(arg_decls + [sub_decl], [trigger], body,
                                       position, info)
            axiom = self.viper.DomainAxiom('union_subtype_' + str(i), forall,
                                           position, info, self.type_domain)
            result.append(axiom)
        return result

    def create_subtype_union_axioms(self,
                                    ctx: Context) -> List['silver.ast.DomainAxiom']:
        """
            Creates UNION_TYPE_SIZE axioms of the following form:
            (forall arg_1: PyType, ..., arg_n: PyType, X: PyType ::
            { issubtype(union_type_n(arg_1, ..., arg_n), X) }
              issubtype(union_type_n(arg_1, ..., arg_n), X) ==
              (true && issubtype(arg_1, X) && ... && issubtype(arg_n, X)))
            """
        result = []
        position, info = self.no_position(ctx), self.no_info(ctx)
        arg_decls = []
        args = []
        arg_subtype = self.viper.TrueLit(position, info)
        sub_decl = self.viper.LocalVarDecl('X', self.type_type(), position,
                                           info)
        sub_var = self.viper.LocalVar('X', self.type_type(), position, info)
        for i in range(1, self.UNION_TYPE_SIZE + 1):
            arg_decl = self.viper.LocalVarDecl('arg_' + str(i), self.type_type(),
                                               position, info)
            arg = self.viper.LocalVar('arg_' + str(i), self.type_type(), position,
                                      info)
            arg_decls.append(arg_decl)
            args.append(arg)
            union = self.viper.DomainFuncApp('union_type_' + str(i), args,
                                             self.type_type(), position,
                                             info, self.type_domain)
            subtype_union = self._issubtype(union, sub_var, ctx, position)
            current_arg_subtype = self._issubtype(arg, sub_var, ctx, position)
            arg_subtype = self.viper.And(arg_subtype, current_arg_subtype,
                                         position, info)
            body = self.viper.EqCmp(subtype_union, arg_subtype, position, info)
            trigger = self.viper.Trigger([subtype_union], position, info)
            forall = self.viper.Forall(arg_decls + [sub_decl], [trigger], body,
                                       position, info)
            axiom = self.viper.DomainAxiom('subtype_union_' + str(i), forall,
                                           position, info, self.type_domain)
            result.append(axiom)
        return result

    def create_tuple_subtype_axiom(self,
                                   ctx: Context) -> 'silver.ast.DomainAxiom':
        """
        (forall seq1: Seq[PyType], seq2: Seq[PyType] ::
            seq1 != seq2 && |seq1| == |seq2| &&
            (forall i: Int :: i >= 0 && i < |seq1| ==>
                              issubtype(seq1[i], seq2[i]))
            ==> issubtype(tuple(seq1), tuple(seq2)))

        """
        name = 'tuple_self_subtype'
        position, info = self.no_position(ctx), self.no_info(ctx)
        seq_type = self.viper.SeqType(self.type_type())
        seq1_decl = self.viper.LocalVarDecl('seq1', seq_type, position, info)
        seq1_ref = self.viper.LocalVar('seq1', seq_type, position, info)
        seq2_decl = self.viper.LocalVarDecl('seq2', seq_type, position, info)
        seq2_ref = self.viper.LocalVar('seq2', seq_type, position, info)
        tuple1 = self.viper.DomainFuncApp('tuple', [seq1_ref],
                                          self.type_type(), position,
                                          info, self.type_domain)
        tuple2 = self.viper.DomainFuncApp('tuple', [seq2_ref],
                                          self.type_type(), position,
                                          info, self.type_domain)

        subtype = self._issubtype(tuple1, tuple2, ctx)
        length1 = self.viper.SeqLength(seq1_ref, position, info)
        length2 = self.viper.SeqLength(seq2_ref, position, info)
        length_eq = self.viper.EqCmp(length1, length2, position, info)
        i_decl = self.viper.LocalVarDecl('i', self.viper.Int, position, info)
        i_ref = self.viper.LocalVar('i', self.viper.Int, position, info)
        i1 = self.viper.SeqIndex(seq1_ref, i_ref, position, info)
        i2 = self.viper.SeqIndex(seq2_ref, i_ref, position, info)
        i_subtype = self._issubtype(i1, i2, ctx)
        i_nonneg = self.viper.GeCmp(i_ref, self.viper.IntLit(0, position, info),
                                    position, info)
        i_lt_length = self.viper.LtCmp(i_ref, length1, position, info)
        i_in_bounds = self.viper.And(i_nonneg, i_lt_length, position, info)
        forall_body = self.viper.Implies(i_in_bounds, i_subtype, position, info)
        rhs_forall = self.viper.Forall([i_decl], [], forall_body, position,
                                       info)
        seqs_different = self.viper.NeCmp(seq1_ref, seq2_ref, position, info)
        seq_restrictions = self.viper.And(seqs_different, length_eq, position,
                                          info)
        rhs = self.viper.And(seq_restrictions, rhs_forall, position, info)
        body = self.viper.Implies(rhs, subtype, position, info)
        body = self.viper.Forall([seq1_decl, seq2_decl], [], body, position,
                                 info)
        result = self.viper.DomainAxiom(name, body, position, info,
                                        self.type_domain)
        return result

    def create_tuple_arg_axiom(self,
                               ctx: Context) -> 'silver.ast.DomainAxiom':
        """
        (forall seq: Seq[PyType], i: Int, Z: PyType ::
          { tuple(seq),tuple_arg(Z, i) }
          issubtype(Z, tuple(seq)) ==> issubtype(tuple_arg(Z, i), seq[i]))
        """
        name = 'tuple_arg_def'
        position, info = self.no_position(ctx), self.no_info(ctx)
        seq_type = self.viper.SeqType(self.type_type())
        z_decl = self.viper.LocalVarDecl('Z', self.type_type(), position, info)
        z_ref = self.viper.LocalVar('Z', self.type_type(), position, info)
        seq_decl = self.viper.LocalVarDecl('seq', seq_type, position, info)
        seq_ref = self.viper.LocalVar('seq', seq_type, position, info)
        i_decl = self.viper.LocalVarDecl('i', self.viper.Int, position, info)
        i_ref = self.viper.LocalVar('i', self.viper.Int, position, info)
        tuple_seq = self.viper.DomainFuncApp('tuple', [seq_ref],
                                             self.type_type(), position, info,
                                             self.type_domain)
        subtype = self._issubtype(z_ref, tuple_seq, ctx)
        arg_args = [z_ref, i_ref]
        arg_func = self.viper.DomainFuncApp('tuple_arg', arg_args,
                                             self.type_type(), position, info,
                                            self.type_domain)
        seq_index = self.viper.SeqIndex(seq_ref, i_ref, position, info)
        rhs = self._issubtype(arg_func, seq_index, ctx)

        body = self.viper.Implies(subtype, rhs, position, info)
        trigger = self.viper.Trigger([tuple_seq, arg_func], position, info)
        body = self.viper.Forall([seq_decl, i_decl, z_decl], [trigger], body,
                                 position, info)
        result = self.viper.DomainAxiom(name, body, position, info,
                                        self.type_domain)
        return result

    def create_tuple_args_axiom(self,
                                   ctx: Context) -> 'silver.ast.DomainAxiom':
        """
        (forall seq: Seq[PyType], Z: PyType :: { issubtype(Z, tuple(seq)) }
          issubtype(Z, tuple(seq)) ==> |tuple_args(Z)| == |seq|)
        """
        name = 'tuple_args_def'
        position, info = self.no_position(ctx), self.no_info(ctx)
        seq_type = self.viper.SeqType(self.type_type())
        z_decl = self.viper.LocalVarDecl('Z', self.type_type(), position, info)
        z_ref = self.viper.LocalVar('Z', self.type_type(), position, info)
        seq_decl = self.viper.LocalVarDecl('seq', seq_type, position, info)
        seq_ref = self.viper.LocalVar('seq', seq_type, position, info)
        tuple_seq = self.viper.DomainFuncApp('tuple', [seq_ref],
                                             self.type_type(), position, info,
                                             self.type_domain)
        subtype = self._issubtype(z_ref, tuple_seq, ctx)
        args_func = self.viper.DomainFuncApp('tuple_args', [z_ref],
                                             seq_type, position, info,
                                             self.type_domain)
        args_func_len = self.viper.SeqLength(args_func, position, info)
        seq_ref_len = self.viper.SeqLength(seq_ref, position, info)
        rhs = self.viper.EqCmp(args_func_len, seq_ref_len, position, info)
        body = self.viper.Implies(subtype, rhs, position, info)
        trigger = self.viper.Trigger([subtype], position, info)
        body = self.viper.Forall([seq_decl, z_decl], [trigger], body, position,
                                 info)
        result = self.viper.DomainAxiom(name, body, position, info,
                                        self.type_domain)
        return result

    def tuple_args_func(self, ctx: Context) -> 'silver.ast.DomainFunc':
        position, info = self.no_position(ctx), self.no_info(ctx)
        args = [self.viper.LocalVarDecl('t', self.type_type(), position, info)]
        result = self.viper.DomainFunc('tuple_args', args,
                                       self.viper.SeqType(self.type_type()),
                                       False, position, info, self.type_domain)
        return result

    def create_type(self, cls: 'PythonClass',
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
        if cls.interface and not cls.superclass:
            subtype_axiom = None
        else:
            subtype_axiom = self.create_subtype_axiom(cls, supertype,
                                                      position, info, ctx)
        funcs = type_funcs
        axioms = [subtype_axiom] if subtype_axiom else []
        if cls.type_vars or cls.name == TUPLE_TYPE:
            funcs.extend(self.create_arg_functions(cls, ctx))
            # create functions for type arguments
            axioms.extend(self.create_arg_axioms(cls, ctx))
            # create axioms that relate arguments to functions
        return funcs, axioms

    def create_arg_functions(self, cls: 'PythonClass',
                             ctx: Context) -> List['silver.ast.DomainFunc']:
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
        type, e.g. for PSeq:
        (forall Z: PyType, arg0: PyType ::
          issubtype(Z, PSeq(arg0)) ==> PSeq_arg(Z, 0) == arg0)
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
        for i, var in enumerate(cls.type_vars):
            args = [z_ref, self.viper.IntLit(i, position, info)]
            current_arg = self.viper.DomainFuncApp(cls.sil_name + '_arg', args,
                                                   self.type_type(), position,
                                                   info, self.type_domain)
            if cls.name == TUPLE_TYPE:
                args = [current_arg, type_args[i]]
                rhs = self._issubtype(current_arg, type_args[i], ctx)
            else:
                rhs = self.viper.EqCmp(current_arg, type_args[i], position,
                                       info)
            implication = self.viper.Implies(subtype, rhs, position, info)
            triggers = [self.viper.Trigger([func_lit, current_arg], position, info)]
            quantifier = self.viper.Forall(decls, triggers, implication, position,
                                           info)
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
        if type_nargs != 0:
            result.append(self.viper.DomainFunc(name + '_basic', [], self.type_type(),
                                                True, position, info, self.type_domain))
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
                   position=None) -> 'silver.ast.DomainFuncApp':
        return self._issubtype_app('issubtype', sub, super, ctx, position)

    def _extends(self, sub: Expr, super: Expr, ctx: Context,
                 position=None) -> 'silver.ast.DomainFuncApp':
        return self._issubtype_app('extends_', sub, super, ctx, position)

    def _isnotsubtype(self, sub: Expr, super: Expr, ctx: Context,
                      position=None) -> 'silver.ast.DomainFuncApp':
        return self._issubtype_app('isnotsubtype', sub, super, ctx, position)

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

    def create_subtype_axiom(self, type: PythonType, supertype: PythonType,
                             position: 'silver.ast.Position',
                             info: 'silver.ast.Info',
                             ctx: Context) -> 'silver.ast.DomainAxiom':
        """
        Creates a domain axiom that indicates a subtype relationship
        between type and supertype, quantified over type variables.

        E.g. for class Sub(Generic[T], Super[T, int]):
        forall arg0: PyType :: {Sub(arg0)}
          extends_(Sub(arg0), Super(arg0, int()))
        """
        type_arg_decls = []
        type_args = []
        ctx.bound_type_vars = {}
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

        supertype_func = self.translate_type_literal(supertype,
                                                     position, ctx)
        body = self._extends(type_func, supertype_func, ctx, position)
        if type.name == TUPLE_TYPE:
            # Special case for tuples:
            # forall args: Seq[PyType] :: { tuple(args) }
            # (forall e: PyType :: (e in args) ==> e == object())
            #                       ==> extends_(tuple(args), object())
            # This way, tuple(Seq(object(), object())) extends object,
            # but tuple(int(), int()) does not, which we need, because types
            # that extend the same supertype are said not to be subtypes of
            # each other by issubtype_exclusion.
            e_decl = self.viper.LocalVarDecl('e', self.type_type(), position,
                                             info)
            e_ref = self.viper.LocalVar('e', self.type_type(), position, info)
            e_contained = self.viper.SeqContains(e_ref, args_ref, position,
                                                 info)
            object_func = self.viper.DomainFuncApp('object', [],
                                                   self.type_type(), position,
                                                   info, self.type_domain)
            e_is_object = self.viper.EqCmp(e_ref, object_func, position, info)
            implication = self.viper.Implies(e_contained, e_is_object, position,
                                             info)
            body_lhs = self.viper.Forall([e_decl], [], implication, position,
                                         info)
            body = self.viper.Implies(body_lhs, body, position, info)
        if type_arg_decls:
            basic_type = self.viper.DomainFuncApp(type.sil_name + '_basic', [],
                                                  self.type_type(), position, info,
                                                  self.type_domain)
        else:
            basic_type = type_func
        type_func_basic = self.viper.DomainFuncApp('get_basic', [type_func],
                                                   self.type_type(), position, info,
                                                   self.type_domain)
        define_basic = self.viper.EqCmp(type_func_basic, basic_type, position, info)
        body = self.viper.And(body, define_basic, position, info)
        if type_arg_decls:
            trigger = self.viper.Trigger([type_func], position, info)
            body = self.viper.Forall(type_arg_decls, [trigger], body, position,
                                     info)
        return self.viper.DomainAxiom('subtype_' + type.sil_name, body,
                                      position, info,
                                      self.type_domain)

    def create_extends_implies_subtype_axiom(self,
            ctx: Context) -> 'silver.ast.DomainAxiom':
        """
        Creates an axiom that states that an extends-relationship between two
        types implies a subtype-relationship:

        forall sub: PyType, sub2: PyType :: { extends_(sub, sub2) }
        extends_(sub, sub2)
        ==>
        issubtype(sub, sub2)
        """
        position, info = self.no_position(ctx), self.no_info(ctx)
        arg_sub = self.viper.LocalVarDecl('sub', self.type_type(), position,
                                          info)
        var_sub = self.viper.LocalVar('sub', self.type_type(), position, info)
        arg_super = self.viper.LocalVarDecl('sub2', self.type_type(), position,
                                            info)
        var_super = self.viper.LocalVar('sub2', self.type_type(), position,
                                        info)
        extends = self._extends(var_sub, var_super, ctx)
        subtype = self._issubtype(var_sub, var_super, ctx)
        implication = self.viper.Implies(extends, subtype, position, info)
        trigger = self.viper.Trigger([extends], position, info)
        body = self.viper.Forall([arg_sub, arg_super], [trigger],
                                 implication, position, info)
        return self.viper.DomainAxiom('extends_implies_subtype', body,
                                      position, info, self.type_domain)

    def create_subtype_exclusion_axiom_2(self,
            ctx: Context) -> 'silver.ast.DomainAxiom':
        """
        forall sub: PyType, super: PyType ::
        { issubtype(sub, super) } { issubtype(super, sub) }
        issubtype(sub, super) && sub != super ==> !issubtype(super, sub)
        """
        position, info = self.no_position(ctx), self.no_info(ctx)
        arg_sub = self.viper.LocalVarDecl('sub', self.type_type(),
                                          position, info)
        var_sub = self.viper.LocalVar('sub', self.type_type(), position, info)
        arg_super = self.viper.LocalVarDecl('super', self.type_type(),
                                            position, info)
        var_super = self.viper.LocalVar('super', self.type_type(),
                                        position, info)
        sub_super = self._issubtype(var_sub, var_super, ctx)
        super_sub = self._issubtype(var_super, var_sub, ctx)
        not_super_sub = self.viper.Not(super_sub, position, info)
        not_equal = self.viper.NeCmp(var_sub, var_super, position, info)
        lhs = self.viper.And(sub_super, not_equal, position, info)
        implication = self.viper.Implies(lhs, not_super_sub, position, info)
        trigger = self.viper.Trigger([sub_super], position, info)
        trigger2 = self.viper.Trigger([super_sub], position, info)
        body = self.viper.Forall([arg_sub, arg_super], [trigger, trigger2],
                                 implication, position, info)
        return self.viper.DomainAxiom('issubtype_exclusion_2', body,
                                      position, info, self.type_domain)

    def create_subtype_exclusion_axiom(
            self, ctx: Context) -> 'silver.ast.DomainAxiom':
        """
        Creates an axiom that states that two types that directly extend
        another type cannot be subtypes of each other:

        forall sub: PyType, sub2: PyType, super: PyType ::
        { extends_(sub, super),extends_(sub2, super) }
        extends_(sub, super) && extends_(sub2, super) && (sub != sub2)
        ==>
        isnotsubtype(sub, sub2) && isnotsubtype(sub2, sub))
        """
        position, info = self.no_position(ctx), self.no_info(ctx)
        arg_sub = self.viper.LocalVarDecl('sub', self.type_type(), position,
                                          info)
        var_sub = self.viper.LocalVar('sub', self.type_type(),
                                      position, info)
        arg_sub2 = self.viper.LocalVarDecl('sub2', self.type_type(),
                                           position, info)
        var_sub2 = self.viper.LocalVar('sub2', self.type_type(), position, info)
        arg_super = self.viper.LocalVarDecl('super', self.type_type(),
                                            position, info)
        var_super = self.viper.LocalVar('super', self.type_type(), position,
                                        info)

        sub_super = self._extends(var_sub, var_super, ctx)
        sub2_super = self._extends(var_sub2, var_super, ctx)
        sub_sub2 = self._isnotsubtype(var_sub, var_sub2, ctx)
        sub2_sub = self._isnotsubtype(var_sub2, var_sub, ctx)
        not_subtypes = self.viper.And(sub_sub2, sub2_sub, position, info)
        subs_not_equal = self.viper.NeCmp(var_sub, var_sub2, position, info)
        extends = self.viper.And(sub_super, sub2_super, position, info)
        lhs = self.viper.And(extends, subs_not_equal, position, info)
        implication = self.viper.Implies(lhs, not_subtypes, position, info)
        trigger = self.viper.Trigger([sub_super, sub2_super], position, info)
        body = self.viper.Forall([arg_sub, arg_sub2, arg_super], [trigger],
                                 implication, position, info)
        return self.viper.DomainAxiom('issubtype_exclusion', body,
                                      position, info, self.type_domain)

    def create_subtype_exclusion_propagation_axiom(self,
            ctx: Context) -> 'silver.ast.DomainAxiom':
        """
        Creates an axiom that propagates the information that two types
        are not subtypes down the type hierarchy:

        forall sub: PyType, middle: PyType, super: PyType ::
        { issubtype(sub, middle),isnotsubtype(middle, super) }
        issubtype(sub, middle) && isnotsubtype(middle, super)
        ==>
        !issubtype(sub, super))
        """
        position, info = self.no_position(ctx), self.no_info(ctx)
        arg_sub = self.viper.LocalVarDecl('sub', self.type_type(), position,
                                          info)
        var_sub = self.viper.LocalVar('sub', self.type_type(), position, info)
        arg_middle = self.viper.LocalVarDecl('middle', self.type_type(),
                                             position, info)
        var_middle = self.viper.LocalVar('middle', self.type_type(),
                                         position, info)
        arg_super = self.viper.LocalVarDecl('super', self.type_type(),
                                            position, info)
        var_super = self.viper.LocalVar('super', self.type_type(),
                                        position, info)

        sub_middle = self._issubtype(var_sub, var_middle, ctx)

        middle_super = self._isnotsubtype(var_middle, var_super, ctx)
        sub_super = self._issubtype(var_sub, var_super, ctx)

        not_sub_super = self.viper.Not(sub_super, position, info)
        implication = self.viper.Implies(
            self.viper.And(sub_middle, middle_super, position, info),
            not_sub_super, position, info)
        trigger = self.viper.Trigger([sub_middle, middle_super],
                                     position, info)
        body = self.viper.Forall([arg_sub, arg_middle, arg_super], [trigger],
                                 implication, position, info)
        return self.viper.DomainAxiom('issubtype_exclusion_propagation', body,
                                      position, info, self.type_domain)

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
        typeof = self.typeof(var_r, ctx)
        subtype = self._issubtype(typeof, none_type, ctx)
        is_null = self.viper.EqCmp(var_r,
                                   self.viper.NullLit(position, info),
                                   position, info)
        biimplication = self.viper.EqCmp(subtype, is_null, position, info)
        trigger = self.viper.Trigger([typeof], position, info)
        body = self.viper.Forall([arg_r], [trigger],
                                 biimplication, position, info)
        return self.viper.DomainAxiom('null_nonetype', body, position, info,
                                      self.type_domain)

    def create_object_type(self, ctx: Context) -> 'silver.ast.DomainFunc':
        return self.create_type_function(OBJECT_TYPE, 0, self.no_position(ctx),
                                         self.no_info(ctx))[0]

    def create_null_type(self, ctx: Context) -> 'silver.ast.DomainFunc':
        return self.create_type_function('NoneType', 0, self.no_position(ctx),
                                         self.no_info(ctx))[0]

    def create_transitivity_axiom(self,
                                  ctx: Context) -> 'silver.ast.DomainAxiom':
        """
        Creates the transitivity axiom for the PyType domain:
        forall sub: PyType, middle: PyType, super: PyType ::
            { issubtype(sub, middle),issubtype(middle, super) }
            issubtype(sub, middle) && issubtype(middle, super)
            ==>
            issubtype(sub, super)
        """
        position, info = self.no_position(ctx), self.no_info(ctx)
        arg_sub = self.viper.LocalVarDecl('sub', self.type_type(),
                                          position, info)
        var_sub = self.viper.LocalVar('sub', self.type_type(), position, info)
        arg_middle = self.viper.LocalVarDecl('middle', self.type_type(),
                                             position, info)
        var_middle = self.viper.LocalVar('middle', self.type_type(),
                                         position, info)
        arg_super = self.viper.LocalVarDecl('super', self.type_type(),
                                            position, info)
        var_super = self.viper.LocalVar('super', self.type_type(),
                                        position, info)

        sub_middle = self._issubtype(var_sub, var_middle, ctx)

        middle_super = self._issubtype(var_middle, var_super, ctx)

        sub_super = self._issubtype(var_sub, var_super, ctx)

        implication = self.viper.Implies(
            self.viper.And(sub_middle, middle_super, position, info),
            sub_super, position, info)
        trigger = self.viper.Trigger([sub_middle, middle_super], position, info)
        body = self.viper.Forall([arg_sub, arg_middle, arg_super], [trigger],
                                 implication, position, info)
        return self.viper.DomainAxiom('issubtype_transitivity', body,
                                      position, info, self.type_domain)

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

    def basic_func(self, ctx: Context) -> 'silver.ast.DomainFunc':
        """
        Creates the get_basic domain function
        """
        t_var = self.viper.LocalVarDecl('t', self.type_type(),
                                          self.no_position(ctx),
                                          self.no_info(ctx))
        return self.viper.DomainFunc('get_basic', [t_var],
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

    def isnotsubtype_func(self, ctx: Context) -> 'silver.ast.DomainFunc':
        return self.subtype_func('isnotsubtype', ctx)

    def extends_func(self, ctx: Context) -> 'silver.ast.DomainFunc':
        return self.subtype_func('extends_', ctx)

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
        if isinstance(type, GenericType) and not type.exact_length:
            assert type.name == TUPLE_TYPE
            seq_type = self.viper.SeqType(self.type_type())
            i_ref = self.viper.LocalVar('i', self.viper.Int, position, info)
            i_decl = self.viper.LocalVarDecl('i', self.viper.Int, position,
                                             info)
            zero = self.viper.IntLit(0, position, info)
            i_ge_zero = self.viper.GeCmp(i_ref, zero, position, info)
            tuple_args = self.viper.DomainFuncApp('tuple_args', [type_func],
                                                  seq_type, position, info,
                                                  self.type_domain)
            tuple_args_len = self.viper.SeqLength(tuple_args, position, info)
            i_lt_len = self.viper.LtCmp(i_ref, tuple_args_len, position, info)
            i_in_bounds = self.viper.And(i_ge_zero, i_lt_len, position, info)
            tuple_arg = self.viper.DomainFuncApp('tuple_arg',
                                                 [type_func, i_ref],
                                                 self.type_type(), position,
                                                 info, self.type_domain)
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
            return forall

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

    def type_comp(self, lhs: Expr, rhs: Expr, ctx: Context, eq=False) -> Expr:
        """
        Creates an expression of the from 'typeof(lhs) == typeof(rhs)'.
        """
        type_func_lhs = self.typeof(lhs, ctx)
        type_func_rhs = self.typeof(rhs, ctx)
        if eq:
            return self.viper.EqCmp(type_func_lhs, type_func_rhs,
                                    self.no_position(ctx), self.no_info(ctx))
        else:
            return self.viper.NeCmp(type_func_lhs, type_func_rhs,
                                    self.no_position(ctx), self.no_info(ctx))

import ast

from py2viper_translation.lib.constants import OBJECT_TYPE, TUPLE_TYPE
from py2viper_translation.lib.program_nodes import (
    GenericType,
    PythonClass,
    PythonType,
    TypeVar,
    UnionType,
)
from py2viper_translation.lib.viper_ast import ViperAST
from py2viper_translation.translators.abstract import Context, Expr
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

    def no_position(self, ctx: Context) -> 'silver.ast.Position':
        return self.translator.no_position(ctx)

    def to_position(self, node: ast.AST, ctx: Context) -> 'silver.ast.Position':
        return self.translator.to_position(node, ctx)

    def no_info(self, ctx: Context) -> 'silver.ast.Position':
        return self.translator.no_info(ctx)

    def get_default_axioms(self,
                           ctx: Context) -> List['silver.ast.DomainAxiom']:
        return [
            self.create_transitivity_axiom(ctx),
            self.create_reflexivity_axiom(ctx),
            self.create_extends_implies_subtype_axiom(ctx),
            self.create_none_type_subtype_axiom(ctx),
            self.create_null_type_axiom(ctx),
            self.create_object_subtype_axiom(ctx),
            self.create_subtype_exclusion_axiom(ctx),
            self.create_subtype_exclusion_axiom_2(ctx),
            self.create_subtype_exclusion_propagation_axiom(ctx),
            self.create_union_extends_axiom(ctx),
            self.create_union_extends2_axiom(ctx),
            self.create_union_not_extends_axiom(ctx),
            self.create_tuple_arg_axiom(ctx),
            self.create_tuple_args_axiom(ctx),
            self.create_tuple_subtype_axiom(ctx),
        ]
        # tuple_arg, tuple_args, union_extends, tuple_subtype

    def get_default_functions(self,
                              ctx: Context) -> List['silver.ast.DomainFunc']:
        result = [
            self.extends_func(ctx),
            self.issubtype_func(ctx),
            self.isnotsubtype_func(ctx),
            self.tuple_args_func(ctx),
            self.typeof_func(ctx),
            self.union_func(ctx)
        ]
        return result

    def union_func(self, ctx: Context) -> 'silver.ast.DomainFunc':
        position, info = self.no_position(ctx), self.no_info(ctx)
        seq_type = self.viper.SeqType(self.type_type())
        seq_decl = self.viper.LocalVarDecl('seq', seq_type, position, info)
        result = self.viper.DomainFunc('union_type', [seq_decl], self.type_type(),
                                       False, position, info, self.type_domain)
        return result

    def create_union_extends2_axiom(self,
                                   ctx: Context) -> 'silver.ast.DomainAxiom':
        """
        axiom union_extends2 {
           (forall seq: Seq[PyType], Z: PyType, X: PyType :: {union_type(seq), extends_(X, Z)} ((Z in seq) && extends_(X, Z)) ==> issubtype(X, union_type(seq)))
        }
        """
        name = 'union_extends2'
        position, info = self.no_position(ctx), self.no_info(ctx)
        seq_type = self.viper.SeqType(self.type_type())
        z_decl = self.viper.LocalVarDecl('Z', self.type_type(), position, info)
        z_ref = self.viper.LocalVar('Z', self.type_type(), position, info)
        x_decl = self.viper.LocalVarDecl('X', self.type_type(), position, info)
        x_ref = self.viper.LocalVar('X', self.type_type(), position, info)
        seq_decl = self.viper.LocalVarDecl('seq', seq_type, position, info)
        seq_ref = self.viper.LocalVar('seq', seq_type, position, info)
        union = self.viper.DomainFuncApp('union_type', [seq_ref], {}, self.type_type(), [seq_ref], position, info, self.type_domain)
        subtype = self.viper.DomainFuncApp('issubtype', [x_ref, union], {}, self.viper.Bool, [x_ref, union], position, info, self.type_domain)
        extends = self.viper.DomainFuncApp('extends_', [x_ref, z_ref], {},
                                           self.viper.Bool, [x_ref, z_ref],
                                           position, info, self.type_domain)
        contains = self.viper.SeqContains(z_ref, seq_ref, position, info)
        lhs = self.viper.And(contains, extends, position, info)
        body = self.viper.Implies(lhs, subtype, position, info)
        trigger = self.viper.Trigger([union, extends], position, info)
        body = self.viper.Forall([seq_decl, z_decl, x_decl], [trigger], body, position, info)
        result = self.viper.DomainAxiom(name, body, position, info,
                                        self.type_domain)
        return result

    def create_union_extends_axiom(self,
                                   ctx: Context) -> 'silver.ast.DomainAxiom':
        """
        axiom union_extends {
            (forall seq: Seq[PyType] :: { union_type(seq) } (forall Z: PyType :: (Z in seq) ==> issubtype(Z, union_type(seq))))
        }
        """
        name = 'union_extends'
        position, info = self.no_position(ctx), self.no_info(ctx)
        seq_type = self.viper.SeqType(self.type_type())
        z_decl = self.viper.LocalVarDecl('Z', self.type_type(), position, info)
        z_ref = self.viper.LocalVar('Z', self.type_type(), position, info)
        seq_decl = self.viper.LocalVarDecl('seq', seq_type, position, info)
        seq_ref = self.viper.LocalVar('seq', seq_type, position, info)
        union = self.viper.DomainFuncApp('union_type', [seq_ref], {}, self.type_type(),
                                         [seq_ref], position, info, self.type_domain)
        extends = self.viper.DomainFuncApp('issubtype', [z_ref, union], {},
                                           self.viper.Bool, [z_ref, union], position,
                                           info, self.type_domain)
        contains = self.viper.SeqContains(z_ref, seq_ref, position, info)

        body = self.viper.Implies(contains, extends, position, info)
        body = self.viper.Forall([z_decl], [], body, position, info)
        trigger = self.viper.Trigger([union], position, info)

        body = self.viper.Forall([seq_decl], [trigger], body,
                                 position, info)
        result = self.viper.DomainAxiom(name, body, position, info,
                                        self.type_domain)
        return result

    def create_union_not_extends_axiom(self,
                                   ctx: Context) -> 'silver.ast.DomainAxiom':
        """
        axiom union_not_extends {
          forall seq: Seq[PyType], Z: PyType :: { issubtype(Z, union_type(seq)) } (forall X: PyType :: (X in seq ==> !issubtype(Z, X))) == !issubtype(Z, union_type(seq))
        }
        """
        name = 'union_not_extends'
        position, info = self.no_position(ctx), self.no_info(ctx)
        seq_type = self.viper.SeqType(self.type_type())
        z_decl = self.viper.LocalVarDecl('Z', self.type_type(), position, info)
        z_ref = self.viper.LocalVar('Z', self.type_type(), position, info)
        x_decl = self.viper.LocalVarDecl('X', self.type_type(), position, info)
        x_ref = self.viper.LocalVar('X', self.type_type(), position, info)
        seq_decl = self.viper.LocalVarDecl('seq', seq_type, position, info)
        seq_ref = self.viper.LocalVar('seq', seq_type, position, info)
        union = self.viper.DomainFuncApp('union_type', [seq_ref], {}, self.type_type(),
                                         [seq_ref], position, info, self.type_domain)
        subtype_z_union = self.viper.DomainFuncApp('issubtype', [z_ref, union], {},
                                                   self.viper.Bool, [z_ref, union], position,
                                                   info, self.type_domain)
        subtype_z_x = self.viper.DomainFuncApp('issubtype', [z_ref, x_ref], {},
                                               self.viper.Bool,
                                               [z_ref, x_ref], position,
                                               info, self.type_domain)
        contains = self.viper.SeqContains(x_ref, seq_ref, position, info)
        not_z_x = self.viper.Not(subtype_z_x, position, info)
        not_z_union = self.viper.Not(subtype_z_union, position, info)
        body = self.viper.Implies(contains, not_z_x, position, info)
        lhs = self.viper.Forall([x_decl], [], body, position, info)
        body = self.viper.EqCmp(lhs, not_z_union, position, info)
        trigger = self.viper.Trigger([subtype_z_union], position, info)

        body = self.viper.Forall([seq_decl, z_decl], [trigger], body,
                                 position, info)
        result = self.viper.DomainAxiom(name, body, position, info,
                                        self.type_domain)
        return result

    def create_tuple_subtype_axiom(self,
                                   ctx: Context) -> 'silver.ast.DomainAxiom':
        name = 'tuple_self_subtype'
        position, info = self.no_position(ctx), self.no_info(ctx)
        seq_type = self.viper.SeqType(self.type_type())
        seq1_decl = self.viper.LocalVarDecl('seq1', seq_type, position, info)
        seq1_ref = self.viper.LocalVar('seq1', seq_type, position, info)
        seq2_decl = self.viper.LocalVarDecl('seq2', seq_type, position, info)
        seq2_ref = self.viper.LocalVar('seq2', seq_type, position, info)
        tuple1 = self.viper.DomainFuncApp('tuple', [seq1_ref], {},
                                          self.type_type(), [seq1_ref], position,
                                          info, self.type_domain)
        tuple2 = self.viper.DomainFuncApp('tuple', [seq2_ref], {},
                                          self.type_type(), [seq2_ref], position,
                                          info, self.type_domain)

        subtype = self.viper.DomainFuncApp('issubtype', [tuple1, tuple2], {},
                                           self.viper.Bool, [tuple1, tuple2],
                                           position, info, self.type_domain)
        length1 = self.viper.SeqLength(seq1_ref, position, info)
        length2 = self.viper.SeqLength(seq2_ref, position, info)
        length_eq = self.viper.EqCmp(length1, length2, position, info)
        i_decl = self.viper.LocalVarDecl('i', self.viper.Int, position, info)
        i_ref = self.viper.LocalVar('i', self.viper.Int, position, info)
        i1 = self.viper.SeqIndex(seq1_ref, i_ref, position, info)
        i2 = self.viper.SeqIndex(seq2_ref, i_ref, position, info)
        i_subtype = self.viper.DomainFuncApp('issubtype', [i1, i2], {}, self.viper.Bool, [i1, i2], position, info, self.type_domain)
        i_nonneg = self.viper.GeCmp(i_ref, self.viper.IntLit(0, position, info),
                                    position, info)
        i_lt_length = self.viper.LtCmp(i_ref, length1, position, info)
        i_in_bounds = self.viper.And(i_nonneg, i_lt_length, position, info)
        forall_body = self.viper.Implies(i_in_bounds, i_subtype, position, info)
        rhs_forall = self.viper.Forall([i_decl], [], forall_body, position, info)
        seqs_different = self.viper.NeCmp(seq1_ref, seq2_ref, position, info)
        seq_restrictions = self.viper.And(seqs_different, length_eq, position, info)
        rhs = self.viper.And(seq_restrictions, rhs_forall, position, info)
        body = self.viper.Implies(rhs, subtype, position, info)
        body = self.viper.Forall([seq1_decl, seq2_decl], [], body, position, info)
        result = self.viper.DomainAxiom(name, body, position, info,
                                        self.type_domain)
        return result

    def create_tuple_arg_axiom(self,
                               ctx: Context) -> 'silver.ast.DomainAxiom':
        name = 'tuple_arg_def'
        position, info = self.no_position(ctx), self.no_info(ctx)
        seq_type = self.viper.SeqType(self.type_type())
        z_decl = self.viper.LocalVarDecl('Z', self.type_type(), position, info)
        z_ref = self.viper.LocalVar('Z', self.type_type(), position, info)
        seq_decl = self.viper.LocalVarDecl('seq', seq_type, position, info)
        seq_ref = self.viper.LocalVar('seq', seq_type, position, info)
        i_decl = self.viper.LocalVarDecl('i', self.viper.Int, position, info)
        i_ref = self.viper.LocalVar('i', self.viper.Int, position, info)
        tuple_seq = self.viper.DomainFuncApp('tuple', [seq_ref], {},
                                             self.type_type(), [seq_ref],
                                             position, info, self.type_domain)
        subtype = self.viper.DomainFuncApp('issubtype', [z_ref, tuple_seq], {},
                                           self.viper.Bool, [z_ref, tuple_seq],
                                           position, info, self.type_domain)
        arg_args = [z_ref, i_ref]
        arg_func = self.viper.DomainFuncApp('tuple_arg', arg_args, {},
                                             self.type_type(), arg_args,
                                             position, info, self.type_domain)
        seq_index = self.viper.SeqIndex(seq_ref, i_ref, position, info)
        rhs = self.viper.DomainFuncApp('issubtype', [arg_func, seq_index], {}, self.viper.Bool, [arg_func, seq_index], position, info, self.type_domain)

        body = self.viper.Implies(subtype, rhs, position, info)
        trigger = self.viper.Trigger([tuple_seq, arg_func], position, info)
        body = self.viper.Forall([seq_decl, i_decl, z_decl], [trigger], body, position, info)
        result = self.viper.DomainAxiom(name, body, position, info,
                                        self.type_domain)
        return result

    def create_tuple_args_axiom(self,
                                   ctx: Context) -> 'silver.ast.DomainAxiom':
        name = 'tuple_args_def'
        position, info = self.no_position(ctx), self.no_info(ctx)
        seq_type = self.viper.SeqType(self.type_type())
        z_decl = self.viper.LocalVarDecl('Z', self.type_type(), position, info)
        z_ref = self.viper.LocalVar('Z', self.type_type(), position, info)
        seq_decl = self.viper.LocalVarDecl('seq', seq_type, position, info)
        seq_ref = self.viper.LocalVar('seq', seq_type, position, info)
        tuple_seq = self.viper.DomainFuncApp('tuple', [seq_ref], {},
                                             self.type_type(), [seq_ref],
                                             position, info, self.type_domain)
        subtype = self.viper.DomainFuncApp('issubtype', [z_ref, tuple_seq], {},
                                           self.viper.Bool, [z_ref, tuple_seq],
                                           position, info, self.type_domain)
        args_func = self.viper.DomainFuncApp('tuple_args', [z_ref], {},
                                             seq_type, [z_ref], position,
                                             info, self.type_domain)
        args_func_len = self.viper.SeqLength(args_func, position, info)
        seq_ref_len = self.viper.SeqLength(seq_ref, position, info)
        rhs = self.viper.EqCmp(args_func_len, seq_ref_len, position, info)
        body = self.viper.Implies(subtype, rhs, position, info)
        trigger = self.viper.Trigger([subtype], position, info)
        body = self.viper.Forall([seq_decl, z_decl], [trigger], body, position, info)
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
            supertype = cls.get_module().global_module.classes[OBJECT_TYPE]
        else:
            supertype = cls.superclass
        position = self.to_position(cls.node, ctx)
        info = self.no_info(ctx)
        type_nargs = len(cls.type_vars) if cls.name != TUPLE_TYPE else -1
        type_func = self.create_type_function(cls.sil_name, type_nargs,
                                              position, info, ctx)
        if cls.interface and not cls.superclass:
            subtype_axiom = None
        else:
            subtype_axiom = self.create_subtype_axiom(cls, supertype,
                                                      position, info, ctx)
        funcs = [type_func]
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
        # issubtype(Z, func(bla)) ==> func1(Z) == bla  # unsound with not-nonvariant type args
        # issubtype(Z, func(bla)) ==> issubtype(func1(Z), bla)  # for not-nonvariant type args
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
        func_lit = self.viper.DomainFuncApp(cls.sil_name, type_args, {},
                                            self.type_type(), type_args,
                                            position, info, self.type_domain)
        subtype_args = [z_ref, func_lit]
        subtype = self.viper.DomainFuncApp('issubtype', subtype_args, {},
                                           self.viper.Bool, subtype_args,
                                           position, info, self.type_domain)
        for i, var in enumerate(cls.type_vars):
            args = [z_ref, self.viper.IntLit(i, position, info)]
            current_arg = self.viper.DomainFuncApp(cls.sil_name + '_arg', args,
                                                   {}, self.type_type(), args,
                                                   position, info,
                                                   self.type_domain)
            if cls.name == TUPLE_TYPE:
                args = [current_arg, type_args[i]]
                rhs = self.viper.DomainFuncApp('issubtype', args, {},
                                               self.viper.Bool, args, position,
                                               info, self.type_domain)
            else:
                rhs = self.viper.EqCmp(current_arg, type_args[i], position,
                                       info)
            implication = self.viper.Implies(subtype, rhs, position, info)
            quantifier = self.viper.Forall(decls, [], implication, position,
                                           info)
            axiom = self.viper.DomainAxiom(cls.sil_name + '_args' + str(i),
                                           quantifier, position, info,
                                           self.type_domain)
            result.append(axiom)
        return result

    def create_type_function(self, name: str, type_nargs: int,
                             position: 'silver.ast.Position',
                             info: 'silver.ast.Info',
                             ctx: Context) -> 'silver.ast.DomainFunc':
        args = []
        if type_nargs == -1:
            seq_type = self.viper.SeqType(self.type_type())
            args.append(self.viper.LocalVarDecl('args', seq_type, position,
                                                info))
        else:
            for i in range(type_nargs):
                args.append(self.viper.LocalVarDecl('arg' + str(i),
                                                    self.type_type(), position,
                                                    info))
        return self.viper.DomainFunc(name, args, self.type_type(),
                                     len(args) == 0, position, info,
                                     self.type_domain)

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

    def create_subtype_axiom(self, type: PythonType, supertype: PythonType,
                             position: 'silver.ast.Position',
                             info: 'silver.ast.Info',
                             ctx: Context) -> 'silver.ast.DomainAxiom':
        """
        Creates a domain axiom that indicates a subtype relationship
        between type and supertype:

        extends_(type(), supertype())
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
                var = self.viper.LocalVar(name, self.type_type(), position, info)
                type_args.append(var)
                type_arg_decls.append(self.viper.LocalVarDecl(name, self.type_type(), position, info))
                ctx.bound_type_vars[(type.name, name)] = var

        type_var = self.viper.LocalVar('class', self.type_type(), position,
                                       info)
        type_func = self.viper.DomainFuncApp(type.sil_name, type_args, {}, self.type_type(), type_args,
                                             position, info, self.type_domain)

        supertype_func = self.translate_type_literal(supertype,
                                                     position, ctx)
        body = self.viper.DomainFuncApp('extends_',
                                        [type_func, supertype_func], {},
                                        self.viper.Bool, [type_var, type_var],
                                        position, info, self.type_domain)
        if type.name == TUPLE_TYPE:
            # (forall e: PyType :: e in args ==> e == object()) ==>
            e_decl = self.viper.LocalVarDecl('e', self.type_type(), position, info)
            e_ref = self.viper.LocalVar('e', self.type_type(), position, info)
            e_contained = self.viper.SeqContains(e_ref, args_ref, position, info)
            object_func = self.viper.DomainFuncApp('object', [], {}, self.type_type(), [], position, info, self.type_domain)
            e_is_object = self.viper.EqCmp(e_ref, object_func, position, info)
            implication = self.viper.Implies(e_contained, e_is_object, position, info)
            body_lhs = self.viper.Forall([e_decl], [], implication, position, info)
            body = self.viper.Implies(body_lhs, body, position, info)
        if type_arg_decls:
            trigger = self.viper.Trigger([type_func], position, info)
            body = self.viper.Forall(type_arg_decls, [trigger], body, position, info)
        return self.viper.DomainAxiom('subtype_' + type.sil_name, body, position, info,
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
        arg_sub = self.viper.LocalVarDecl('sub', self.type_type(),
                                          self.no_position(ctx),
                                          self.no_info(ctx))
        var_sub = self.viper.LocalVar('sub', self.type_type(),
                                      self.no_position(ctx), self.no_info(ctx))
        arg_super = self.viper.LocalVarDecl('sub2', self.type_type(),
                                            self.no_position(ctx),
                                            self.no_info(ctx))
        var_super = self.viper.LocalVar('sub2', self.type_type(),
                                        self.no_position(ctx),
                                        self.no_info(ctx))
        extends = self.viper.DomainFuncApp('extends_',
                                           [var_sub, var_super], {},
                                           self.viper.Bool,
                                           [var_sub, var_super],
                                           self.no_position(ctx),
                                           self.no_info(ctx), self.type_domain)
        subtype = self.viper.DomainFuncApp('issubtype',
                                           [var_sub, var_super], {},
                                           self.viper.Bool,
                                           [var_sub, var_super],
                                           self.no_position(ctx),
                                           self.no_info(ctx), self.type_domain)
        implication = self.viper.Implies(extends, subtype,
                                         self.no_position(ctx),
                                         self.no_info(ctx))
        trigger = self.viper.Trigger([extends], self.no_position(ctx),
                                     self.no_info(ctx))
        body = self.viper.Forall([arg_sub, arg_super], [trigger],
                                 implication, self.no_position(ctx),
                                 self.no_info(ctx))
        return self.viper.DomainAxiom('extends_implies_subtype', body,
                                      self.no_position(ctx), self.no_info(ctx),
                                      self.type_domain)

    def create_subtype_exclusion_axiom_2(self,
            ctx: Context) -> 'silver.ast.DomainAxiom':
        arg_sub = self.viper.LocalVarDecl('sub', self.type_type(),
                                          self.no_position(ctx),
                                          self.no_info(ctx))
        var_sub = self.viper.LocalVar('sub', self.type_type(),
                                      self.no_position(ctx), self.no_info(ctx))
        arg_super = self.viper.LocalVarDecl('super', self.type_type(),
                                            self.no_position(ctx),
                                            self.no_info(ctx))
        var_super = self.viper.LocalVar('super', self.type_type(),
                                        self.no_position(ctx),
                                        self.no_info(ctx))
        sub_super = self.viper.DomainFuncApp('issubtype',
                                             [var_sub, var_super], {},
                                             self.viper.Bool,
                                             [var_sub, var_super],
                                             self.no_position(ctx),
                                             self.no_info(ctx),
                                             self.type_domain)
        super_sub = self.viper.DomainFuncApp('issubtype',
                                             [var_super, var_sub], {},
                                             self.viper.Bool,
                                             [var_super, var_sub],
                                             self.no_position(ctx),
                                             self.no_info(ctx),
                                             self.type_domain)
        not_super_sub = self.viper.Not(super_sub, self.no_position(ctx),
                                       self.no_info(ctx))
        not_equal = self.viper.NeCmp(var_sub, var_super, self.no_position(ctx),
                                     self.no_info(ctx))
        lhs = self.viper.And(sub_super, not_equal, self.no_position(ctx),
                             self.no_info(ctx))
        implication = self.viper.Implies(lhs, not_super_sub,
                                         self.no_position(ctx),
                                         self.no_info(ctx))
        trigger = self.viper.Trigger([sub_super],
                                     self.no_position(ctx),
                                     self.no_info(ctx))
        trigger2 = self.viper.Trigger([super_sub],
                                      self.no_position(ctx),
                                      self.no_info(ctx))
        body = self.viper.Forall([arg_sub, arg_super], [trigger, trigger2],
                                 implication, self.no_position(ctx),
                                 self.no_info(ctx))
        return self.viper.DomainAxiom('issubtype_exclusion_2', body,
                                      self.no_position(ctx), self.no_info(ctx),
                                      self.type_domain)

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
        arg_sub = self.viper.LocalVarDecl('sub', self.type_type(),
                                          self.no_position(ctx),
                                          self.no_info(ctx))
        var_sub = self.viper.LocalVar('sub', self.type_type(),
                                      self.no_position(ctx), self.no_info(ctx))
        arg_sub2 = self.viper.LocalVarDecl('sub2', self.type_type(),
                                           self.no_position(ctx),
                                           self.no_info(ctx))
        var_sub2 = self.viper.LocalVar('sub2', self.type_type(),
                                       self.no_position(ctx),
                                       self.no_info(ctx))
        arg_super = self.viper.LocalVarDecl('super', self.type_type(),
                                            self.no_position(ctx),
                                            self.no_info(ctx))
        var_super = self.viper.LocalVar('super', self.type_type(),
                                        self.no_position(ctx),
                                        self.no_info(ctx))

        sub_super = self.viper.DomainFuncApp('extends_',
                                             [var_sub, var_super], {},
                                             self.viper.Bool,
                                             [var_sub, var_super],
                                             self.no_position(ctx),
                                             self.no_info(ctx),
                                             self.type_domain)
        sub2_super = self.viper.DomainFuncApp('extends_',
                                              [var_sub2, var_super], {},
                                              self.viper.Bool,
                                              [var_sub2, var_super],
                                              self.no_position(ctx),
                                              self.no_info(ctx),
                                              self.type_domain)
        sub_sub2 = self.viper.DomainFuncApp('isnotsubtype', [var_sub, var_sub2],
                                            {}, self.viper.Bool,
                                            [var_sub, var_sub2],
                                            self.no_position(ctx),
                                            self.no_info(ctx), self.type_domain)
        sub2_sub = self.viper.DomainFuncApp('isnotsubtype', [var_sub2, var_sub],
                                            {}, self.viper.Bool,
                                            [var_sub2, var_sub],
                                            self.no_position(ctx),
                                            self.no_info(ctx), self.type_domain)
        not_subtypes = self.viper.And(sub_sub2, sub2_sub, self.no_position(ctx),
                                      self.no_info(ctx))
        subs_not_equal = self.viper.NeCmp(var_sub, var_sub2,
                                          self.no_position(ctx),
                                          self.no_info(ctx))
        extends = self.viper.And(sub_super, sub2_super, self.no_position(ctx),
                                 self.no_info(ctx))
        lhs = self.viper.And(extends, subs_not_equal, self.no_position(ctx),
                             self.no_info(ctx))
        implication = self.viper.Implies(lhs, not_subtypes,
                                         self.no_position(ctx),
                                         self.no_info(ctx))
        trigger = self.viper.Trigger([sub_super, sub2_super],
                                     self.no_position(ctx),
                                     self.no_info(ctx))
        body = self.viper.Forall([arg_sub, arg_sub2, arg_super], [trigger],
                                 implication, self.no_position(ctx),
                                 self.no_info(ctx))
        return self.viper.DomainAxiom('issubtype_exclusion', body,
                                      self.no_position(ctx), self.no_info(ctx),
                                      self.type_domain)

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
        arg_sub = self.viper.LocalVarDecl('sub', self.type_type(),
                                          self.no_position(ctx),
                                          self.no_info(ctx))
        var_sub = self.viper.LocalVar('sub', self.type_type(),
                                      self.no_position(ctx), self.no_info(ctx))
        arg_middle = self.viper.LocalVarDecl('middle', self.type_type(),
                                             self.no_position(ctx),
                                             self.no_info(ctx))
        var_middle = self.viper.LocalVar('middle', self.type_type(),
                                         self.no_position(ctx),
                                         self.no_info(ctx))
        arg_super = self.viper.LocalVarDecl('super', self.type_type(),
                                            self.no_position(ctx),
                                            self.no_info(ctx))
        var_super = self.viper.LocalVar('super', self.type_type(),
                                        self.no_position(ctx),
                                        self.no_info(ctx))

        sub_middle = self.viper.DomainFuncApp('issubtype',
                                              [var_sub, var_middle], {},
                                              self.viper.Bool,
                                              [var_sub, var_middle],
                                              self.no_position(ctx),
                                              self.no_info(ctx),
                                              self.type_domain)
        middle_super = self.viper.DomainFuncApp('isnotsubtype',
                                                [var_middle, var_super], {},
                                                self.viper.Bool,
                                                [var_middle, var_super],
                                                self.no_position(ctx),
                                                self.no_info(ctx),
                                                self.type_domain)
        sub_super = self.viper.DomainFuncApp('issubtype', [var_sub, var_super],
                                             {}, self.viper.Bool,
                                             [var_sub, var_super],
                                             self.no_position(ctx),
                                             self.no_info(ctx),
                                             self.type_domain)
        not_sub_super = self.viper.Not(sub_super, self.no_position(ctx),
                                       self.no_info(ctx))
        implication = self.viper.Implies(
            self.viper.And(sub_middle, middle_super, self.no_position(ctx),
                           self.no_info(ctx)), not_sub_super,
            self.no_position(ctx),
            self.no_info(ctx))
        trigger = self.viper.Trigger([sub_middle, middle_super],
                                     self.no_position(ctx), self.no_info(ctx))
        body = self.viper.Forall([arg_sub, arg_middle, arg_super], [trigger],
                                 implication, self.no_position(ctx),
                                 self.no_info(ctx))
        return self.viper.DomainAxiom('issubtype_exclusion_propagation', body,
                                      self.no_position(ctx), self.no_info(ctx),
                                      self.type_domain)

    def create_null_type_axiom(self, ctx: Context) -> 'silver.ast.DomainAxiom':
        """
        Creates an axiom that states that the type of null is None:

        forall r: Ref :: {issubtype(typeof(r), NoneType())}
        issubtype(typeof(r), NoneType()) <==> r == null
        """
        arg_r = self.viper.LocalVarDecl('r', self.viper.Ref,
                                        self.no_position(ctx),
                                        self.no_info(ctx))
        var_r = self.viper.LocalVar('r', self.viper.Ref,
                                    self.no_position(ctx), self.no_info(ctx))
        none_type = self.viper.DomainFuncApp('NoneType', [], {},
                                             self.type_type(), [],
                                             self.no_position(ctx),
                                             self.no_info(ctx),
                                             self.type_domain)
        typeof = self.viper.DomainFuncApp('typeof', [var_r], {},
                                          self.type_type(), [var_r],
                                          self.no_position(ctx),
                                          self.no_info(ctx),
                                          self.type_domain)
        subtype = self.viper.DomainFuncApp('issubtype',
                                           [typeof, none_type], {},
                                           self.viper.Bool,
                                           [typeof, none_type],
                                           self.no_position(ctx),
                                           self.no_info(ctx), self.type_domain)
        is_null = self.viper.EqCmp(var_r,
                                   self.viper.NullLit(self.no_position(ctx),
                                                      self.no_info(ctx)),
                                   self.no_position(ctx), self.no_info(ctx))
        biimplication = self.viper.EqCmp(subtype, is_null,
                                         self.no_position(ctx),
                                         self.no_info(ctx))
        trigger = self.viper.Trigger([typeof], self.no_position(ctx),
                                     self.no_info(ctx))
        body = self.viper.Forall([arg_r], [trigger],
                                 biimplication, self.no_position(ctx),
                                 self.no_info(ctx))
        return self.viper.DomainAxiom('null_nonetype', body,
                                      self.no_position(ctx), self.no_info(ctx),
                                      self.type_domain)

    def create_none_type_subtype_axiom(
            self, ctx: Context) -> 'silver.ast.DomainAxiom':
        """
        Creates an axiom that states that no type is a subtype of NoneType:

        forall sub: PyType, r: Ref ::
        { issubtype(typeof(r), sub) }
        issubtype(typeof(r), sub) && (sub != NoneType()) ==> (r != null)
        """
        arg_sub = self.viper.LocalVarDecl('sub', self.type_type(),
                                          self.no_position(ctx),
                                          self.no_info(ctx))
        var_sub = self.viper.LocalVar('sub', self.type_type(),
                                      self.no_position(ctx), self.no_info(ctx))
        arg_r = self.viper.LocalVarDecl('r', self.viper.Ref,
                                        self.no_position(ctx),
                                        self.no_info(ctx))
        var_r = self.viper.LocalVar('r', self.viper.Ref,
                                    self.no_position(ctx), self.no_info(ctx))
        none_type = self.viper.DomainFuncApp('NoneType', [], {},
                                             self.type_type(), [],
                                             self.no_position(ctx),
                                             self.no_info(ctx),
                                             self.type_domain)
        typeof = self.viper.DomainFuncApp('typeof', [var_r], {},
                                          self.type_type(), [var_r],
                                          self.no_position(ctx),
                                          self.no_info(ctx),
                                          self.type_domain)
        subtype = self.viper.DomainFuncApp('issubtype',
                                           [typeof, var_sub], {},
                                           self.viper.Bool,
                                           [typeof, var_sub],
                                           self.no_position(ctx),
                                           self.no_info(ctx), self.type_domain)
        not_none = self.viper.NeCmp(var_sub, none_type, self.no_position(ctx),
                                    self.no_info(ctx))
        not_null = self.viper.NeCmp(var_r,
                                    self.viper.NullLit(self.no_position(ctx),
                                                       self.no_info(ctx)),
                                    self.no_position(ctx), self.no_info(ctx))
        implication = self.viper.Implies(self.viper.And(subtype, not_none,
                                                        self.no_position(ctx),
                                                        self.no_info(ctx)),
                                         not_null, self.no_position(ctx),
                                         self.no_info(ctx))
        trigger = self.viper.Trigger([subtype], self.no_position(ctx),
                                     self.no_info(ctx))
        body = self.viper.Forall([arg_sub, arg_r], [trigger],
                                 implication, self.no_position(ctx),
                                 self.no_info(ctx))
        return self.viper.DomainAxiom('none_type_subtype', body,
                                      self.no_position(ctx), self.no_info(ctx),
                                      self.type_domain)

    def create_object_type(self, ctx: Context) -> 'silver.ast.DomainFunc':
        return self.create_type_function(OBJECT_TYPE, 0, self.no_position(ctx),
                                         self.no_info(ctx))

    def create_null_type(self, ctx: Context) -> 'silver.ast.DomainFunc':
        return self.create_type_function('NoneType', 0, self.no_position(ctx),
                                         self.no_info(ctx))

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
        arg_sub = self.viper.LocalVarDecl('sub', self.type_type(),
                                          self.no_position(ctx),
                                          self.no_info(ctx))
        var_sub = self.viper.LocalVar('sub', self.type_type(),
                                      self.no_position(ctx), self.no_info(ctx))
        arg_middle = self.viper.LocalVarDecl('middle', self.type_type(),
                                             self.no_position(ctx),
                                             self.no_info(ctx))
        var_middle = self.viper.LocalVar('middle', self.type_type(),
                                         self.no_position(ctx),
                                         self.no_info(ctx))
        arg_super = self.viper.LocalVarDecl('super', self.type_type(),
                                            self.no_position(ctx),
                                            self.no_info(ctx))
        var_super = self.viper.LocalVar('super', self.type_type(),
                                        self.no_position(ctx),
                                        self.no_info(ctx))

        sub_middle = self.viper.DomainFuncApp('issubtype',
                                              [var_sub, var_middle], {},
                                              self.viper.Bool,
                                              [var_sub, var_middle],
                                              self.no_position(ctx),
                                              self.no_info(ctx),
                                              self.type_domain)
        middle_super = self.viper.DomainFuncApp('issubtype',
                                                [var_middle, var_super], {},
                                                self.viper.Bool,
                                                [var_middle, var_super],
                                                self.no_position(ctx),
                                                self.no_info(ctx),
                                                self.type_domain)
        sub_super = self.viper.DomainFuncApp('issubtype', [var_sub, var_super],
                                             {}, self.viper.Bool,
                                             [var_sub, var_super],
                                             self.no_position(ctx),
                                             self.no_info(ctx),
                                             self.type_domain)
        implication = self.viper.Implies(
            self.viper.And(sub_middle, middle_super, self.no_position(ctx),
                           self.no_info(ctx)), sub_super, self.no_position(ctx),
            self.no_info(ctx))
        trigger = self.viper.Trigger([sub_middle, middle_super],
                                     self.no_position(ctx), self.no_info(ctx))
        body = self.viper.Forall([arg_sub, arg_middle, arg_super], [trigger],
                                 implication, self.no_position(ctx),
                                 self.no_info(ctx))
        return self.viper.DomainAxiom('issubtype_transitivity', body,
                                      self.no_position(ctx), self.no_info(ctx),
                                      self.type_domain)

    def create_reflexivity_axiom(self,
                                 ctx: Context) -> 'silver.ast.DomainAxiom':
        """
        Creates the reflexivity axiom for the PyType domain:
        forall type: PyType :: { issubtype(type, type) } issubtype(type, type)
        """
        arg = self.viper.LocalVarDecl('type_', self.type_type(),
                                      self.no_position(ctx), self.no_info(ctx))
        var = self.viper.LocalVar('type_', self.type_type(),
                                  self.no_position(ctx), self.no_info(ctx))
        reflexive_subtype = self.viper.DomainFuncApp('issubtype', [var, var],
                                                     {}, self.viper.Bool,
                                                     [var, var],
                                                     self.no_position(ctx),
                                                     self.no_info(ctx),
                                                     self.type_domain)
        trigger_exp = reflexive_subtype
        trigger = self.viper.Trigger([trigger_exp], self.no_position(ctx),
                                     self.no_info(ctx))
        body = self.viper.Forall([arg], [trigger], reflexive_subtype,
                                 self.no_position(ctx), self.no_info(ctx))
        return self.viper.DomainAxiom('issubtype_reflexivity', body,
                                      self.no_position(ctx), self.no_info(ctx),
                                      self.type_domain)

    def create_object_subtype_axiom(self,
                                    ctx: Context) -> 'silver.ast.DomainAxiom':
        """
        Creates the axiom saying that all types are subtypes of object:
        forall type: PyType :: { issubtype(type, object()) }
        issubtype(type, object())
        """
        arg = self.viper.LocalVarDecl('type_', self.type_type(),
                                      self.no_position(ctx), self.no_info(ctx))
        var = self.viper.LocalVar('type_', self.type_type(),
                                  self.no_position(ctx), self.no_info(ctx))
        object_type = self.viper.DomainFuncApp('object', [], {},
                                               self.type_type(), [],
                                               self.no_position(ctx),
                                               self.no_info(ctx),
                                               self.type_domain)
        object_subtype = self.viper.DomainFuncApp('issubtype',
                                                  [var, object_type],
                                                  {}, self.viper.Bool,
                                                  [var, object_type],
                                                  self.no_position(ctx),
                                                  self.no_info(ctx),
                                                  self.type_domain)
        trigger_exp = object_subtype
        trigger = self.viper.Trigger([trigger_exp], self.no_position(ctx),
                                     self.no_info(ctx))
        body = self.viper.Forall([arg], [trigger], object_subtype,
                                 self.no_position(ctx), self.no_info(ctx))
        return self.viper.DomainAxiom('issubtype_object', body,
                                      self.no_position(ctx), self.no_info(ctx),
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

    def isnotsubtype_func(self, ctx: Context) -> 'silver.ast.DomainFunc':
        return self.subtype_func('isnotsubtype', ctx)

    def extends_func(self, ctx: Context) -> 'silver.ast.DomainFunc':
        return self.subtype_func('extends_', ctx)

    def dynamic_type_check(self, lhs: 'Expr',
                           type: 'Expr', position: 'silver.ast.Position',
                           ctx: Context):
        type_func = self.viper.DomainFuncApp('typeof', [lhs], {},
                                             self.type_type(), [lhs],
                                             self.no_position(ctx),
                                             self.no_info(ctx),
                                             self.type_domain)
        result = self.viper.EqCmp(type_func, type, self.no_position(ctx),
                                  self.no_info(ctx))
        return result

    def typeof(self, arg: 'Expr', ctx: Context) -> 'Expr':
        type_func = self.viper.DomainFuncApp('typeof', [arg], {},
                                             self.type_type(), [arg],
                                             self.no_position(ctx),
                                             self.no_info(ctx),
                                             self.type_domain)
        return type_func

    def subtype_check(self, type_func: 'Expr', type: 'PythonType',
                      position: 'silver.ast.Position',
                      ctx: Context, concrete=False) -> Expr:
        info = self.no_info(ctx)
        if isinstance(type, GenericType) and not type.exact_length:
            assert type.name == TUPLE_TYPE
            seq_type = self.viper.SeqType(self.type_type())
            i_ref = self.viper.LocalVar('i', self.viper.Int, position, info)
            i_decl = self.viper.LocalVarDecl('i', self.viper.Int, position,
                                             info)
            zero = self.viper.IntLit(0, position, info)
            i_ge_zero = self.viper.GeCmp(i_ref, zero, position, info)
            tuple_args = self.viper.DomainFuncApp('tuple_args', [type_func], {},
                                                  seq_type, [type_func],
                                                  position, info,
                                                  self.type_domain)
            tuple_args_len = self.viper.SeqLength(tuple_args, position, info)
            i_lt_len = self.viper.LtCmp(i_ref, tuple_args_len, position, info)
            i_in_bounds = self.viper.And(i_ge_zero, i_lt_len, position, info)
            tuple_arg = self.viper.DomainFuncApp('tuple_arg',
                                                 [type_func, i_ref], {},
                                                 self.type_type(),
                                                 [type_func, i_ref], position,
                                                 info, self.type_domain)
            arg_lit = self.translate_type_literal(type.type_args[0], position,
                                                  ctx)
            if concrete:
                subtype = self.viper.EqCmp(tuple_arg, arg_lit, position, info)
            else:
                subtype = self.viper.DomainFuncApp('issubtype',
                                                   [tuple_arg, arg_lit], {},
                                                   self.viper.Bool,
                                                   [tuple_arg, arg_lit], position,
                                                   info, self.type_domain)
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
            result = self.viper.DomainFuncApp('issubtype',
                                              [type_func, supertype_func], {},
                                              self.viper.Bool,
                                              [var_sub, var_super],
                                              position,
                                              self.no_info(ctx),
                                              self.type_domain)
        return result

    def type_check(self, lhs: 'Expr', type: 'PythonType',
                   position: 'silver.ast.Position',
                   ctx: Context, concrete=False) -> Expr:
        """
        Creates an expression checking if the given lhs expression
        is of the given type
        """
        info = self.no_info(ctx)
        type_func = self.viper.DomainFuncApp('typeof', [lhs], {},
                                             self.type_type(), [lhs],
                                             position, info,
                                             self.type_domain)
        return self.subtype_check(type_func, type, position, ctx,
                                  concrete=concrete)

    def translate_type_literal(self, type: 'PythonType', position: 'Position',
                               ctx: Context, alias=None) -> Expr:
        if isinstance(type, TypeVar):
            return ctx.bound_type_vars[(type.target_type.name, type.name)]
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
        if type.name in {TUPLE_TYPE, 'Union'}:
            seq_arg = self.viper.ExplicitSeq(args, position, self.no_info(ctx))
            args = [seq_arg]
        if type.name == 'Union':
            type_func_name = 'union_type'
        else:
            type_func_name = type.sil_name
        type_func = self.viper.DomainFuncApp(type_func_name, args, {},
                                             self.type_type(), args,
                                             position,
                                             self.no_info(ctx),
                                             self.type_domain)
        return type_func

    def get_type_arg(self, type_expr: Expr, target_type: PythonType,
                     index: int, ctx: Context) -> Expr:
        arg_func_name = target_type.sil_name + '_arg'
        index_lit = self.viper.IntLit(index, self.no_position(ctx),
                                      self.no_info(ctx))
        args = [type_expr, index_lit]
        result = self.viper.DomainFuncApp(arg_func_name, args, {},
                                          self.type_type(), args,
                                          self.no_position(ctx),
                                          self.no_info(ctx),
                                          self.type_domain)
        return result

    def get_ref_type_arg(self, target_expr: Expr, target_type: PythonType,
                         index: int, ctx: Context):
        typeof = self.viper.DomainFuncApp('typeof', [target_expr], {},
                                          self.type_type(), [target_expr],
                                          self.no_position(ctx),
                                          self.no_info(ctx),
                                          self.type_domain)
        return self.get_type_arg(typeof, target_type, index, ctx)

    def type_comp(self, lhs: Expr, rhs: Expr, ctx: Context, eq=False) -> Expr:
        """
        Creates an expression of the from 'typeof(lhs) == typeof(rhs)'.
        """
        type_func_lhs = self.viper.DomainFuncApp('typeof', [lhs], {},
                                                 self.type_type(), [lhs],
                                                 self.no_position(ctx),
                                                 self.no_info(ctx),
                                                 self.type_domain)
        type_func_rhs = self.viper.DomainFuncApp('typeof', [rhs], {},
                                                 self.type_type(), [lhs],
                                                 self.no_position(ctx),
                                                 self.no_info(ctx),
                                                 self.type_domain)
        if eq:
            return self.viper.EqCmp(type_func_lhs, type_func_rhs,
                                    self.no_position(ctx), self.no_info(ctx))
        else:
            return self.viper.NeCmp(type_func_lhs, type_func_rhs,
                                    self.no_position(ctx), self.no_info(ctx))

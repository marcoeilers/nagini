import ast

from py2viper_translation.lib.constants import OBJECT_TYPE
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
            self.create_subtype_exclusion_axiom(ctx),
            self.create_subtype_exclusion_axiom_2(ctx),
            self.create_subtype_exclusion_propagation_axiom(ctx)
        ]

    def get_default_functions(self,
                              ctx: Context) -> List['silver.ast.DomainFunc']:
        result = [
            # self.create_null_type(ctx),
            self.extends_func(ctx),
            self.issubtype_func(ctx),
            self.isnotsubtype_func(ctx),
            self.typeof_func(ctx),
            # self.type_arg_func(ctx),
            # self.type_nargs_func(ctx),
            # self.create_object_type(ctx)
        ]
        result += self.type_arg_funcs(ctx)
        result += self.type_nargs_funcs(ctx)
        return result

    def create_type(self, cls: 'PythonClass',
                    ctx: Context) -> Tuple['silver.ast.DomainFunc',
                                           'silver.ast.DomainAxiom']:
        """
        Creates the type domain function and subtype axiom for this class
        """

        supertype = OBJECT_TYPE if not cls.superclass else cls.superclass.sil_name
        position = self.to_position(cls.node, ctx)
        info = self.no_info(ctx)
        type_func = self.create_type_function(cls.sil_name, position, info, ctx)
        if cls.interface:
            if cls.superclass:
                subtype_axiom = self.create_subtype_axiom(cls.sil_name,
                                                          supertype,
                                                          position, info, ctx)
            else:
                subtype_axiom = None
        else:
            subtype_axiom = self.create_subtype_axiom(cls.sil_name, supertype,
                                                      position, info, ctx)
        return type_func, subtype_axiom

    def create_type_function(self, name: str, position: 'silver.ast.Position',
                             info: 'silver.ast.Info',
                             ctx: Context) -> 'silver.ast.DomainFunc':
        return self.viper.DomainFunc(name, [], self.type_type(), True, position,
                                     info, self.type_domain)

    def create_type_domain(self, type_funcs: List['silver.ast.DomainFunc'],
                           type_axioms: List['silver.ast.DomainAxiom'],
                           ctx: Context) -> 'silver.ast.Domain':
        return self.viper.Domain(self.type_domain, type_funcs, type_axioms,
                                 [], self.no_position(ctx), self.no_info(ctx))

    def type_type(self) -> 'silver.ast.DomainType':
        """
        Creates a reference to the domain type we use for the Python types
        """
        return self.viper.DomainType(self.type_domain, {}, [])

    def create_subtype_axiom(self, type: str, supertype: str,
                             position: 'silver.ast.Position',
                             info: 'silver.ast.Info',
                             ctx: Context) -> 'silver.ast.DomainAxiom':
        """
        Creates a domain axiom that indicates a subtype relationship
        between type and supertype:

        extends_(type(), supertype())
        """
        type_var = self.viper.LocalVar('class', self.type_type(), position,
                                       info)
        type_func = self.viper.DomainFuncApp(type, [], {}, self.type_type(), [],
                                             position, info, self.type_domain)
        supertype_func = self.viper.DomainFuncApp(supertype, [], {},
                                                  self.type_type(), [],
                                                  position, info,
                                                  self.type_domain)
        body = self.viper.DomainFuncApp('extends_',
                                        [type_func, supertype_func], {},
                                        self.viper.Bool, [type_var, type_var],
                                        position, info, self.type_domain)
        return self.viper.DomainAxiom('subtype_' + type, body, position, info,
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

    def create_subtype_exclusion_axiom(self,
                                       ctx: Context) -> 'silver.ast.DomainAxiom':
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

        typeof(null) == NoneType()
        """
        null = self.viper.NullLit(self.no_position(ctx), self.no_info(ctx))
        type_func = self.viper.DomainFuncApp('typeof', [null], {},
                                             self.type_type(), [null],
                                             self.no_position(ctx),
                                             self.no_info(ctx),
                                             self.type_domain)
        none_type = self.viper.DomainFuncApp('NoneType', [], {},
                                             self.type_type(), [],
                                             self.no_position(ctx),
                                             self.no_info(ctx),
                                             self.type_domain)
        eq = self.viper.EqCmp(type_func, none_type, self.no_position(ctx),
                              self.no_info(ctx))
        return self.viper.DomainAxiom('null_nonetype', eq,
                                      self.no_position(ctx), self.no_info(ctx),
                                      self.type_domain)

    def create_none_type_subtype_axiom(self,
                                       ctx: Context) -> 'silver.ast.DomainAxiom':
        """
        Creates an axiom that states that no type is a subtype of NoneType:

        forall sub: PyType ::
        { issubtype(sub, NoneType()) }
        !issubtype(sub, NoneType())
        """
        arg_sub = self.viper.LocalVarDecl('sub', self.type_type(),
                                          self.no_position(ctx),
                                          self.no_info(ctx))
        var_sub = self.viper.LocalVar('sub', self.type_type(),
                                      self.no_position(ctx), self.no_info(ctx))
        none_type = self.viper.DomainFuncApp('NoneType', [], {},
                                             self.type_type(), [],
                                             self.no_position(ctx),
                                             self.no_info(ctx),
                                             self.type_domain)
        subtype = self.viper.DomainFuncApp('issubtype',
                                           [var_sub, none_type], {},
                                           self.viper.Bool,
                                           [var_sub, none_type],
                                           self.no_position(ctx),
                                           self.no_info(ctx), self.type_domain)
        not_subtype = self.viper.Not(subtype, self.no_position(ctx),
                                     self.no_info(ctx))
        trigger = self.viper.Trigger([subtype], self.no_position(ctx),
                                     self.no_info(ctx))
        body = self.viper.Forall([arg_sub], [trigger],
                                 not_subtype, self.no_position(ctx),
                                 self.no_info(ctx))
        return self.viper.DomainAxiom('none_type_subtype', body,
                                      self.no_position(ctx), self.no_info(ctx),
                                      self.type_domain)

    def create_object_type(self, ctx: Context) -> 'silver.ast.DomainFunc':
        return self.create_type_function(OBJECT_TYPE, self.no_position(ctx),
                                         self.no_info(ctx))

    def create_null_type(self, ctx: Context) -> 'silver.ast.DomainFunc':
        return self.create_type_function('NoneType', self.no_position(ctx),
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
                                        self.no_position(ctx), self.no_info(ctx))

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
        arg = self.viper.LocalVarDecl('type', self.type_type(),
                                      self.no_position(ctx), self.no_info(ctx))
        var = self.viper.LocalVar('type', self.type_type(),
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

    def type_arg_funcs(self, ctx: Context) -> List['silver.ast.DomainFunc']:
        result = []
        for n in range(1, 6):
            result.append(self.type_arg_func(n, ctx))
        return result

    def type_arg_func(self, n: int, ctx: Context) -> 'silver.ast.DomainFunc':
        """
        Creates the get_type_arg domain function.
        """
        obj_var = self.viper.LocalVarDecl('obj', self.viper.Ref,
                                          self.no_position(ctx),
                                          self.no_info(ctx))
        args = [obj_var]
        for i in range(n):
            name = 'index' + str(i)
            index_var = self.viper.LocalVarDecl(name, self.viper.Int,
                                                self.no_position(ctx),
                                                self.no_info(ctx))
            args.append(index_var)
        name = 'get_type_arg' + str(n)
        result = self.viper.DomainFunc(name, args,
                                       self.type_type(), False,
                                       self.no_position(ctx), self.no_info(ctx),
                                       self.type_domain)
        return result

    def type_nargs_funcs(self, ctx: Context) -> List['silver.ast.DomainFunc']:
        result = []
        for n in range(6):
            result.append(self.type_nargs_func(n, ctx))
        return result

    def type_nargs_func(self, n: int, ctx: Context) -> 'silver.ast.DomainFunc':
        """
        Creates the get_type_arg domain function.
        """
        obj_var = self.viper.LocalVarDecl('obj', self.viper.Ref,
                                          self.no_position(ctx),
                                          self.no_info(ctx))
        args = [obj_var]
        for i in range(n):
            name = 'index' + str(i)
            index_var = self.viper.LocalVarDecl(name, self.viper.Int,
                                                self.no_position(ctx),
                                                self.no_info(ctx))
            args.append(index_var)
        name = 'get_type_nargs' + str(n)
        result = self.viper.DomainFunc(name, args,
                                       self.viper.Int, False,
                                       self.no_position(ctx), self.no_info(ctx),
                                       self.type_domain)
        return result

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

    def type_check(self, lhs: 'Expr', type: 'PythonType',
                   ctx: Context) -> Expr:
        """
        Creates an expression checking if the given lhs expression
        is of the given type
        """
        type_func = self.viper.DomainFuncApp('typeof', [lhs], {},
                                             self.type_type(), [lhs],
                                             self.no_position(ctx),
                                             self.no_info(ctx),
                                             self.type_domain)
        supertype_func = self.viper.DomainFuncApp(type.sil_name, [], {},
                                                  self.type_type(), [],
                                                  self.no_position(ctx),
                                                  self.no_info(ctx),
                                                  self.type_domain)
        var_sub = self.viper.LocalVar('sub', self.type_type(),
                                      self.no_position(ctx), self.no_info(ctx))
        var_super = self.viper.LocalVar('super', self.type_type(),
                                        self.no_position(ctx),
                                        self.no_info(ctx))
        result = self.viper.DomainFuncApp('issubtype',
                                          [type_func, supertype_func], {},
                                          self.viper.Bool,
                                          [var_sub, var_super],
                                          self.no_position(ctx),
                                          self.no_info(ctx),
                                          self.type_domain)
        return result

    def type_arg_check(self, lhs: Expr, arg: 'PythonType',
                       indices: List['Expr'], ctx: Context) -> 'Expr':

        name = 'get_type_arg' + str(len(indices))
        args = [lhs] + indices
        type_arg_func = self.viper.DomainFuncApp(name,
                                                 args,
                                                 {}, self.type_type(),
                                                 args,
                                                 self.no_position(ctx),
                                                 self.no_info(ctx),
                                                 self.type_domain)
        type_func = self.viper.DomainFuncApp(arg.sil_name, [], {},
                                             self.type_type(), [],
                                             self.no_position(ctx),
                                             self.no_info(ctx),
                                             self.type_domain)
        eq = self.viper.EqCmp(type_arg_func, type_func, self.no_position(ctx),
                              self.no_info(ctx))
        return eq

    def type_nargs_check(self, lhs: Expr, nargs: int,
                         indices: List['Expr'], ctx: Context) -> 'Expr':
        name = 'get_type_nargs' + str(len(indices))
        args = [lhs] + indices
        type_arg_func = self.viper.DomainFuncApp(name,
                                                 args,
                                                 {}, self.viper.Int,
                                                 args,
                                                 self.no_position(ctx),
                                                 self.no_info(ctx),
                                                 self.type_domain)
        nargs_lit = self.viper.IntLit(nargs, self.no_position(ctx),
                                      self.no_info(ctx))
        eq = self.viper.EqCmp(type_arg_func, nargs_lit, self.no_position(ctx),
                              self.no_info(ctx))
        return eq

    def concrete_type_check(self, lhs: Expr, type: 'PythonClass',
                            ctx: Context) -> Expr:
        """
        Creates an expression checking if the given lhs expression
        is of the given type
        """
        type_func = self.viper.DomainFuncApp('typeof', [lhs], {},
                                             self.type_type(), [lhs],
                                             self.no_position(ctx),
                                             self.no_info(ctx),
                                             self.type_domain)
        supertype_func = self.viper.DomainFuncApp(type.sil_name, [], {},
                                                  self.type_type(), [],
                                                  self.no_position(ctx),
                                                  self.no_info(ctx),
                                                  self.type_domain)
        cmp = self.viper.EqCmp(type_func, supertype_func, self.no_position(ctx),
                               self.no_info(ctx))
        return cmp

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

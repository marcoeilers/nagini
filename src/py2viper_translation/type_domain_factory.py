import ast

from typing import List, Tuple
from py2viper_translation.viper_ast import ViperAST


class TypeDomainFactory:
    """
    Creates domain functions and axioms that represent the Python/mypy type
    system within Viper.
    """
    def __init__(self, viper: ViperAST, translator: 'Translator'):
        self.viper = viper
        self.typedomain = 'PyType'
        self.translator = translator

    def noposition(self, ctx):
        return self.translator.noposition(ctx)

    def to_position(self, node: ast.AST, ctx):
        return self.translator.to_position(node, ctx)

    def noinfo(self, ctx):
        return self.translator.noinfo(ctx)

    def get_default_axioms(self, ctx) -> List['silver.ast.DomainAxiom']:
        return [
            self.create_transitivity_axiom(ctx),
            self.create_reflexivity_axiom(ctx),
            self.create_extends_implies_subtype_axiom(ctx),
            self.create_none_type_subtype_axiom(ctx),
            self.create_null_type_axiom(ctx),
            self.create_subtype_exclusion_axiom(ctx),
            self.create_subtype_exclusion_propagation_axiom(ctx)
        ]

    def get_default_functions(self, ctx) -> List['silver.ast.DomainFunc']:
        return [
            # self.create_null_type(ctx),
            self.extends_func(ctx),
            self.issubtype_func(ctx),
            self.isnotsubtype_func(ctx),
            self.typeof_func(ctx),
            # self.create_object_type(ctx)
        ]

    def create_type(self, cls: 'PythonClass', ctx) -> Tuple['silver.ast.DomainFunc',
                                                     'silver.ast.DomainAxiom']:
        """
        Creates the type domain function and subtype axiom for this class
        """

        supertype = 'object' if not cls.superclass else cls.superclass.sil_name
        position = self.to_position(cls.node, ctx)
        info = self.noinfo(ctx)
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
                             info: 'silver.ast.Info', ctx) -> 'silver.ast.DomainFunc':
        return self.viper.DomainFunc(name, [], self.typetype(), True, position,
                                     info, self.typedomain)

    def create_type_domain(self, type_funcs, type_axioms, ctx):
        return self.viper.Domain(self.typedomain, type_funcs, type_axioms,
                                     [], self.noposition(ctx), self.noinfo(ctx))

    def typetype(self) -> 'silver.ast.DomainType':
        """
        Creates a reference to the domain type we use for the Python types
        """
        return self.viper.DomainType(self.typedomain, {}, [])

    def create_subtype_axiom(self, type, supertype, position,
                             info, ctx) -> 'silver.ast.DomainAxiom':
        """
        Creates a domain axiom that indicates a subtype relationship
        between type and supertype:

        extends_(type(), supertype())
        """
        type_var = self.viper.LocalVar('class', self.typetype(), position, info)
        type_func = self.viper.DomainFuncApp(type, [], {}, self.typetype(), [],
                                             position, info, self.typedomain)
        supertype_func = self.viper.DomainFuncApp(supertype, [], {},
                                                  self.typetype(), [], position,
                                                  info, self.typedomain)
        body = self.viper.DomainFuncApp('extends_',
                                        [type_func, supertype_func], {},
                                        self.viper.Bool, [type_var, type_var],
                                        position, info, self.typedomain)
        return self.viper.DomainAxiom('subtype_' + type, body, position, info,
                                      self.typedomain)

    def create_extends_implies_subtype_axiom(self, ctx) -> 'silver.ast.DomainAxiom':
        """
        Creates an axiom that states that an extends-relationship between two
        types implies a subtype-relationship:

        forall sub: PyType, sub2: PyType :: { extends_(sub, sub2) }
        extends_(sub, sub2)
        ==>
        issubtype(sub, sub2)
        """
        arg_sub = self.viper.LocalVarDecl('sub', self.typetype(),
                                          self.noposition(ctx),
                                          self.noinfo(ctx))
        var_sub = self.viper.LocalVar('sub', self.typetype(),
                                      self.noposition(ctx), self.noinfo(ctx))
        arg_super = self.viper.LocalVarDecl('sub2', self.typetype(),
                                            self.noposition(ctx),
                                            self.noinfo(ctx))
        var_super = self.viper.LocalVar('sub2', self.typetype(),
                                        self.noposition(ctx),
                                        self.noinfo(ctx))
        extends = self.viper.DomainFuncApp('extends_',
                                           [var_sub, var_super], {},
                                           self.viper.Bool,
                                           [var_sub, var_super],
                                           self.noposition(ctx),
                                           self.noinfo(ctx), self.typedomain)
        subtype = self.viper.DomainFuncApp('issubtype',
                                           [var_sub, var_super], {},
                                           self.viper.Bool,
                                           [var_sub, var_super],
                                           self.noposition(ctx),
                                           self.noinfo(ctx), self.typedomain)
        implication = self.viper.Implies(extends, subtype, self.noposition(ctx),
                                         self.noinfo(ctx))
        trigger = self.viper.Trigger([extends], self.noposition(ctx), self.noinfo(ctx))
        body = self.viper.Forall([arg_sub, arg_super], [trigger],
                                 implication, self.noposition(ctx),
                                 self.noinfo(ctx))
        return self.viper.DomainAxiom('extends_implies_subtype', body,
                                      self.noposition(ctx), self.noinfo(ctx),
                                      self.typedomain)

    def create_subtype_exclusion_axiom(self, ctx) -> 'silver.ast.DomainAxiom':
        """
        Creates an axiom that states that two types that directly extend
        another type cannot be subtypes of each other:

        forall sub: PyType, sub2: PyType, super: PyType ::
        { extends_(sub, super),extends_(sub2, super) }
        extends_(sub, super) && extends_(sub2, super) && (sub != sub2)
        ==>
        isnotsubtype(sub, sub2) && isnotsubtype(sub2, sub))
        """
        arg_sub = self.viper.LocalVarDecl('sub', self.typetype(),
                                          self.noposition(ctx),
                                          self.noinfo(ctx))
        var_sub = self.viper.LocalVar('sub', self.typetype(),
                                      self.noposition(ctx), self.noinfo(ctx))
        arg_sub2 = self.viper.LocalVarDecl('sub2', self.typetype(),
                                           self.noposition(ctx),
                                           self.noinfo(ctx))
        var_sub2 = self.viper.LocalVar('sub2', self.typetype(),
                                       self.noposition(ctx),
                                       self.noinfo(ctx))
        arg_super = self.viper.LocalVarDecl('super', self.typetype(),
                                            self.noposition(ctx),
                                            self.noinfo(ctx))
        var_super = self.viper.LocalVar('super', self.typetype(),
                                        self.noposition(ctx), self.noinfo(ctx))

        sub_super = self.viper.DomainFuncApp('extends_',
                                             [var_sub, var_super], {},
                                             self.viper.Bool,
                                             [var_sub, var_super],
                                             self.noposition(ctx),
                                             self.noinfo(ctx), self.typedomain)
        sub2_super = self.viper.DomainFuncApp('extends_',
                                              [var_sub2, var_super], {},
                                              self.viper.Bool,
                                              [var_sub2, var_super],
                                              self.noposition(ctx),
                                              self.noinfo(ctx), self.typedomain)
        sub_sub2 = self.viper.DomainFuncApp('isnotsubtype', [var_sub, var_sub2],
                                            {}, self.viper.Bool,
                                            [var_sub, var_sub2],
                                            self.noposition(ctx),
                                            self.noinfo(ctx), self.typedomain)
        sub2_sub = self.viper.DomainFuncApp('isnotsubtype', [var_sub2, var_sub],
                                            {}, self.viper.Bool,
                                            [var_sub2, var_sub],
                                            self.noposition(ctx),
                                            self.noinfo(ctx), self.typedomain)
        not_subtypes = self.viper.And(sub_sub2, sub2_sub, self.noposition(ctx),
                                      self.noinfo(ctx))
        subs_not_equal = self.viper.NeCmp(var_sub, var_sub2, self.noposition(ctx),
                                          self.noinfo(ctx))
        extends = self.viper.And(sub_super, sub2_super, self.noposition(ctx),
                                 self.noinfo(ctx))
        lhs = self.viper.And(extends, subs_not_equal, self.noposition(ctx),
                             self.noinfo(ctx))
        implication = self.viper.Implies(lhs, not_subtypes, self.noposition(ctx),
                                         self.noinfo(ctx))
        trigger = self.viper.Trigger([sub_super, sub2_super], self.noposition(ctx),
                                     self.noinfo(ctx))
        body = self.viper.Forall([arg_sub, arg_sub2, arg_super], [trigger],
                                 implication, self.noposition(ctx),
                                 self.noinfo(ctx))
        return self.viper.DomainAxiom('issubtype_exclusion', body,
                                      self.noposition(ctx), self.noinfo(ctx),
                                      self.typedomain)

    def create_subtype_exclusion_propagation_axiom(self, ctx) \
            -> 'silver.ast.DomainAxiom':
        """
        Creates an axiom that propagates the information that two types
        are not subtypes down the type hierarchy:

        forall sub: PyType, middle: PyType, super: PyType ::
        { issubtype(sub, middle),isnotsubtype(middle, super) }
        issubtype(sub, middle) && isnotsubtype(middle, super)
        ==>
        !issubtype(sub, super))
        """
        arg_sub = self.viper.LocalVarDecl('sub', self.typetype(),
                                          self.noposition(ctx),
                                          self.noinfo(ctx))
        var_sub = self.viper.LocalVar('sub', self.typetype(),
                                      self.noposition(ctx), self.noinfo(ctx))
        arg_middle = self.viper.LocalVarDecl('middle', self.typetype(),
                                             self.noposition(ctx),
                                             self.noinfo(ctx))
        var_middle = self.viper.LocalVar('middle', self.typetype(),
                                         self.noposition(ctx),
                                         self.noinfo(ctx))
        arg_super = self.viper.LocalVarDecl('super', self.typetype(),
                                            self.noposition(ctx),
                                            self.noinfo(ctx))
        var_super = self.viper.LocalVar('super', self.typetype(),
                                        self.noposition(ctx), self.noinfo(ctx))

        sub_middle = self.viper.DomainFuncApp('issubtype',
                                              [var_sub, var_middle], {},
                                              self.viper.Bool,
                                              [var_sub, var_middle],
                                              self.noposition(ctx),
                                              self.noinfo(ctx), self.typedomain)
        middle_super = self.viper.DomainFuncApp('isnotsubtype',
                                                [var_middle, var_super], {},
                                                self.viper.Bool,
                                                [var_middle, var_super],
                                                self.noposition(ctx),
                                                self.noinfo(ctx), self.typedomain)
        sub_super = self.viper.DomainFuncApp('issubtype', [var_sub, var_super],
                                             {}, self.viper.Bool,
                                             [var_sub, var_super],
                                             self.noposition(ctx),
                                             self.noinfo(ctx), self.typedomain)
        not_sub_super = self.viper.Not(sub_super, self.noposition(ctx),
                                       self.noinfo(ctx))
        implication = self.viper.Implies(
            self.viper.And(sub_middle, middle_super, self.noposition(ctx),
                           self.noinfo(ctx)), not_sub_super, self.noposition(ctx),
            self.noinfo(ctx))
        trigger = self.viper.Trigger([sub_middle, middle_super], self.noposition(ctx), self.noinfo(ctx))
        body = self.viper.Forall([arg_sub, arg_middle, arg_super], [trigger],
                                 implication, self.noposition(ctx),
                                 self.noinfo(ctx))
        return self.viper.DomainAxiom('issubtype_exclusion_propagation', body,
                                      self.noposition(ctx), self.noinfo(ctx),
                                      self.typedomain)

    def create_null_type_axiom(self, ctx) -> 'silver.ast.DomainAxiom':
        """
        Creates an axiom that states that the type of null is None:

        typeof(null) == NoneType()
        """
        null = self.viper.NullLit(self.noposition(ctx), self.noinfo(ctx))
        type_func = self.viper.DomainFuncApp('typeof', [null], {},
                                             self.typetype(), [null],
                                             self.noposition(ctx),
                                             self.noinfo(ctx), self.typedomain)
        none_type = self.viper.DomainFuncApp('NoneType', [], {},
                                             self.typetype(), [],
                                             self.noposition(ctx), self.noinfo(ctx),
                                             self.typedomain)
        eq = self.viper.EqCmp(type_func, none_type, self.noposition(ctx),
                              self.noinfo(ctx))
        return self.viper.DomainAxiom('null_nonetype', eq, self.noposition(ctx),
                                      self.noinfo(ctx), self.typedomain)

    def create_none_type_subtype_axiom(self, ctx) -> 'silver.ast.DomainAxiom':
        """
        Creates an axiom that states that no type is a subtype of NoneType:

        forall sub: PyType ::
        { issubtype(sub, NoneType()) }
        !issubtype(sub, NoneType())
        """
        arg_sub = self.viper.LocalVarDecl('sub', self.typetype(),
                                          self.noposition(ctx),
                                          self.noinfo(ctx))
        var_sub = self.viper.LocalVar('sub', self.typetype(),
                                      self.noposition(ctx), self.noinfo(ctx))
        none_type = self.viper.DomainFuncApp('NoneType', [], {},
                                             self.typetype(), [],
                                             self.noposition(ctx), self.noinfo(ctx),
                                             self.typedomain)
        subtype = self.viper.DomainFuncApp('issubtype',
                                           [var_sub, none_type], {},
                                           self.viper.Bool,
                                           [var_sub, none_type],
                                           self.noposition(ctx),
                                           self.noinfo(ctx), self.typedomain)
        not_subtype = self.viper.Not(subtype, self.noposition(ctx), self.noinfo(ctx))
        trigger = self.viper.Trigger([subtype], self.noposition(ctx), self.noinfo(ctx))
        body = self.viper.Forall([arg_sub], [trigger],
                                 not_subtype, self.noposition(ctx),
                                 self.noinfo(ctx))
        return self.viper.DomainAxiom('none_type_subtype', body,
                                      self.noposition(ctx), self.noinfo(ctx),
                                      self.typedomain)

    def create_object_type(self, ctx) -> 'silver.ast.DomainFunc':
        return self.create_type_function('object', self.noposition(ctx),
                                         self.noinfo(ctx))

    def create_null_type(self, ctx) -> 'silver.ast.DomainFunc':
        return self.create_type_function('NoneType', self.noposition(ctx),
                                         self.noinfo(ctx))

    def create_transitivity_axiom(self, ctx) -> 'silver.ast.DomainAxiom':
        """
        Creates the transitivity axiom for the PyType domain:
        forall sub: PyType, middle: PyType, super: PyType ::
            { issubtype(sub, middle),issubtype(middle, super) }
            issubtype(sub, middle) && issubtype(middle, super)
            ==>
            issubtype(sub, super)
        """
        arg_sub = self.viper.LocalVarDecl('sub', self.typetype(),
                                          self.noposition(ctx),
                                          self.noinfo(ctx))
        var_sub = self.viper.LocalVar('sub', self.typetype(),
                                      self.noposition(ctx), self.noinfo(ctx))
        arg_middle = self.viper.LocalVarDecl('middle', self.typetype(),
                                             self.noposition(ctx),
                                             self.noinfo(ctx))
        var_middle = self.viper.LocalVar('middle', self.typetype(),
                                         self.noposition(ctx),
                                         self.noinfo(ctx))
        arg_super = self.viper.LocalVarDecl('super', self.typetype(),
                                            self.noposition(ctx),
                                            self.noinfo(ctx))
        var_super = self.viper.LocalVar('super', self.typetype(),
                                        self.noposition(ctx), self.noinfo(ctx))

        sub_middle = self.viper.DomainFuncApp('issubtype',
                                              [var_sub, var_middle], {},
                                              self.viper.Bool,
                                              [var_sub, var_middle],
                                              self.noposition(ctx),
                                              self.noinfo(ctx), self.typedomain)
        middle_super = self.viper.DomainFuncApp('issubtype',
                                                [var_middle, var_super], {},
                                                self.viper.Bool,
                                                [var_middle, var_super],
                                                self.noposition(ctx),
                                                self.noinfo(ctx), self.typedomain)
        sub_super = self.viper.DomainFuncApp('issubtype', [var_sub, var_super],
                                             {}, self.viper.Bool,
                                             [var_sub, var_super],
                                             self.noposition(ctx),
                                             self.noinfo(ctx), self.typedomain)
        implication = self.viper.Implies(
            self.viper.And(sub_middle, middle_super, self.noposition(ctx),
                           self.noinfo(ctx)), sub_super, self.noposition(ctx),
            self.noinfo(ctx))
        trigger = self.viper.Trigger([sub_middle, middle_super],
                                     self.noposition(ctx), self.noinfo(ctx))
        body = self.viper.Forall([arg_sub, arg_middle, arg_super], [trigger],
                                 implication, self.noposition(ctx),
                                 self.noinfo(ctx))
        return self.viper.DomainAxiom('issubtype_transitivity', body,
                                      self.noposition(ctx), self.noinfo(ctx),
                                      self.typedomain)

    def create_reflexivity_axiom(self, ctx) -> 'silver.ast.DomainAxiom':
        """
        Creates the reflexivity axiom for the PyType domain:
        forall type: PyType :: { issubtype(type, type) } issubtype(type, type)
        """
        arg = self.viper.LocalVarDecl('type', self.typetype(),
                                      self.noposition(ctx), self.noinfo(ctx))
        var = self.viper.LocalVar('type', self.typetype(),
                                  self.noposition(ctx), self.noinfo(ctx))
        reflexive_subtype = self.viper.DomainFuncApp('issubtype', [var, var],
                                                     {}, self.viper.Bool,
                                                     [var, var],
                                                     self.noposition(ctx),
                                                     self.noinfo(ctx),
                                                     self.typedomain)
        trigger_exp = reflexive_subtype
        trigger = self.viper.Trigger([trigger_exp], self.noposition(ctx),
                                     self.noinfo(ctx))
        body = self.viper.Forall([arg], [trigger], reflexive_subtype,
                                 self.noposition(ctx), self.noinfo(ctx))
        return self.viper.DomainAxiom('issubtype_reflexivity', body,
                                      self.noposition(ctx), self.noinfo(ctx),
                                      self.typedomain)

    def typeof_func(self, ctx) -> 'silver.ast.DomainFunc':
        """
        Creates the typeof domain function
        """
        obj_var = self.viper.LocalVarDecl('obj', self.viper.Ref,
                                          self.noposition(ctx),
                                          self.noinfo(ctx))
        return self.viper.DomainFunc('typeof', [obj_var],
                                     self.typetype(), False,
                                     self.noposition(ctx), self.noinfo(ctx),
                                     self.typedomain)

    def subtype_func(self, name: str, ctx) -> 'silver.ast.DomainFunc':
        """
        Creates the issubtype, extends and isnotsubtype domain functions.
        """
        sub_var = self.viper.LocalVarDecl('sub', self.typetype(),
                                          self.noposition(ctx),
                                          self.noinfo(ctx))
        super_var = self.viper.LocalVarDecl('super', self.typetype(),
                                            self.noposition(ctx),
                                            self.noinfo(ctx))
        return self.viper.DomainFunc(name, [sub_var, super_var],
                                     self.viper.Bool, False,
                                     self.noposition(ctx), self.noinfo(ctx),
                                     self.typedomain)

    def issubtype_func(self, ctx) -> 'silver.ast.DomainFunc':
        return self.subtype_func('issubtype', ctx)

    def isnotsubtype_func(self, ctx) -> 'silver.ast.DomainFunc':
        return self.subtype_func('isnotsubtype', ctx)

    def extends_func(self, ctx) -> 'silver.ast.DomainFunc':
        return self.subtype_func('extends_', ctx)

    def has_type(self, lhs: 'Expr', type: 'PythonClass', ctx):
        """
        Creates an expression checking if the given lhs expression
        is of the given type
        """
        type_func = self.viper.DomainFuncApp('typeof', [lhs], {},
                                             self.typetype(), [lhs],
                                             self.noposition(ctx),
                                             self.noinfo(ctx), self.typedomain)
        supertype_func = self.viper.DomainFuncApp(type.sil_name, [], {},
                                                  self.typetype(), [],
                                                  self.noposition(ctx),
                                                  self.noinfo(ctx),
                                                  self.typedomain)
        var_sub = self.viper.LocalVar('sub', self.typetype(),
                                      self.noposition(ctx), self.noinfo(ctx))
        var_super = self.viper.LocalVar('super', self.typetype(),
                                        self.noposition(ctx), self.noinfo(ctx))
        subtype_func = self.viper.DomainFuncApp('issubtype',
                                                [type_func, supertype_func], {},
                                                self.viper.Bool,
                                                [var_sub, var_super],
                                                self.noposition(ctx),
                                                self.noinfo(ctx), self.typedomain)
        return subtype_func

    def has_concrete_type(self, lhs: 'Expr', type: 'PythonClass', ctx):
        """
        Creates an expression checking if the given lhs expression
        is of the given type
        """
        type_func = self.viper.DomainFuncApp('typeof', [lhs], {},
                                             self.typetype(), [lhs],
                                             self.noposition(ctx),
                                             self.noinfo(ctx), self.typedomain)
        supertype_func = self.viper.DomainFuncApp(type.sil_name, [], {},
                                                  self.typetype(), [],
                                                  self.noposition(ctx),
                                                  self.noinfo(ctx),
                                                  self.typedomain)
        cmp = self.viper.EqCmp(type_func, supertype_func, self.noposition(ctx),
                               self.noinfo(ctx))
        return cmp
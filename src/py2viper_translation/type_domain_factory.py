import ast

from typing import List, Tuple
from py2viper_translation.viper_ast import ViperAST


class TypeDomainFactory:
    def __init__(self, viper: ViperAST, translator: 'Translator'):
        self.viper = viper
        self.typedomain = 'PyType'
        self.translator = translator

    def noposition(self):
        return self.translator.noposition()

    def to_position(self, node: ast.AST):
        return self.translator.to_position(node)

    def noinfo(self):
        return self.translator.noinfo()

    def get_default_axioms(self) -> List['silver.ast.DomainAxiom']:
        return [
            self.create_transitivity_axiom(),
            self.create_reflexivity_axiom(),
            self.create_extends_implies_subtype_axiom(),
            self.create_none_type_subtype_axiom(),
            self.create_null_type_axiom(),
            self.create_subtype_exclusion_axiom(),
            self.create_subtype_exclusion_propagation_axiom()
        ]

    def get_default_functions(self) -> List['silver.ast.DomainFunc']:
        return [
            self.create_null_type(),
            self.extends_func(),
            self.issubtype_func(),
            self.isnotsubtype_func(),
            self.typeof_func(),
            self.create_object_type()
        ]

    def create_type(self, cls: 'PythonClass') -> Tuple['silver.ast.DomainFunc',
                                                     'silver.ast.DomainAxiom']:
        """
        Creates the type domain function and subtype axiom for this class
        """

        supertype = 'object' if not cls.superclass else cls.superclass.sil_name
        position = self.to_position(cls.node)
        info = self.noinfo()
        return (self.create_type_function(cls.sil_name, position, info),
                self.create_subtype_axiom(cls.sil_name, supertype, position,
                                          info))

    def create_type_function(self, name: str, position: 'silver.ast.Position',
                             info: 'silver.ast.Info') -> 'silver.ast.DomainFunc':
        return self.viper.DomainFunc(name, [], self.typetype(), True, position,
                                     info, self.typedomain)

    def typetype(self) -> 'silver.ast.DomainType':
        """
        Creates a reference to the domain type we use for the Python types
        """
        return self.viper.DomainType(self.typedomain, {}, [])

    def create_subtype_axiom(self, type, supertype, position,
                             info) -> 'silver.ast.DomainAxiom':
        """
        Creates a domain axiom that indicates a subtype relationship
        between type and supertype
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

    def create_extends_implies_subtype_axiom(self) -> 'silver.ast.DomainAxiom':
        arg_sub = self.viper.LocalVarDecl('sub', self.typetype(),
                                          self.noposition(),
                                          self.noinfo())
        var_sub = self.viper.LocalVar('sub', self.typetype(),
                                      self.noposition(), self.noinfo())
        arg_super = self.viper.LocalVarDecl('sub2', self.typetype(),
                                            self.noposition(),
                                            self.noinfo())
        var_super = self.viper.LocalVar('sub2', self.typetype(),
                                        self.noposition(),
                                        self.noinfo())
        extends = self.viper.DomainFuncApp('extends_',
                                           [var_sub, var_super], {},
                                           self.viper.Bool,
                                           [var_sub, var_super],
                                           self.noposition(),
                                           self.noinfo(), self.typedomain)
        subtype = self.viper.DomainFuncApp('issubtype',
                                           [var_sub, var_super], {},
                                           self.viper.Bool,
                                           [var_sub, var_super],
                                           self.noposition(),
                                           self.noinfo(), self.typedomain)
        implication = self.viper.Implies(extends, subtype, self.noposition(),
                                         self.noinfo())
        trigger = self.viper.Trigger([extends], self.noposition(), self.noinfo())
        body = self.viper.Forall([arg_sub, arg_super], [trigger],
                                 implication, self.noposition(),
                                 self.noinfo())
        return self.viper.DomainAxiom('extends_implies_subtype', body,
                                      self.noposition(), self.noinfo(),
                                      self.typedomain)

    def create_subtype_exclusion_axiom(self) -> 'silver.ast.DomainAxiom':
        arg_sub = self.viper.LocalVarDecl('sub', self.typetype(),
                                          self.noposition(),
                                          self.noinfo())
        var_sub = self.viper.LocalVar('sub', self.typetype(),
                                      self.noposition(), self.noinfo())
        arg_sub2 = self.viper.LocalVarDecl('sub2', self.typetype(),
                                           self.noposition(),
                                           self.noinfo())
        var_sub2 = self.viper.LocalVar('sub2', self.typetype(),
                                       self.noposition(),
                                       self.noinfo())
        arg_super = self.viper.LocalVarDecl('super', self.typetype(),
                                            self.noposition(),
                                            self.noinfo())
        var_super = self.viper.LocalVar('super', self.typetype(),
                                        self.noposition(), self.noinfo())

        sub_super = self.viper.DomainFuncApp('extends_',
                                             [var_sub, var_super], {},
                                             self.viper.Bool,
                                             [var_sub, var_super],
                                             self.noposition(),
                                             self.noinfo(), self.typedomain)
        sub2_super = self.viper.DomainFuncApp('extends_',
                                              [var_sub2, var_super], {},
                                              self.viper.Bool,
                                              [var_sub2, var_super],
                                              self.noposition(),
                                              self.noinfo(), self.typedomain)
        sub_sub2 = self.viper.DomainFuncApp('isnotsubtype', [var_sub, var_sub2],
                                            {}, self.viper.Bool,
                                            [var_sub, var_sub2],
                                            self.noposition(),
                                            self.noinfo(), self.typedomain)
        sub2_sub = self.viper.DomainFuncApp('isnotsubtype', [var_sub2, var_sub],
                                            {}, self.viper.Bool,
                                            [var_sub2, var_sub],
                                            self.noposition(),
                                            self.noinfo(), self.typedomain)
        not_subtypes = self.viper.And(sub_sub2, sub2_sub, self.noposition(),
                                      self.noinfo())
        subs_not_equal = self.viper.NeCmp(var_sub, var_sub2, self.noposition(),
                                          self.noinfo())
        extends = self.viper.And(sub_super, sub2_super, self.noposition(),
                                 self.noinfo())
        lhs = self.viper.And(extends, subs_not_equal, self.noposition(),
                             self.noinfo())
        implication = self.viper.Implies(lhs, not_subtypes, self.noposition(),
                                         self.noinfo())
        trigger = self.viper.Trigger([sub_super, sub2_super], self.noposition(),
                                     self.noinfo())
        body = self.viper.Forall([arg_sub, arg_sub2, arg_super], [trigger],
                                 implication, self.noposition(),
                                 self.noinfo())
        return self.viper.DomainAxiom('issubtype_exclusion', body,
                                      self.noposition(), self.noinfo(),
                                      self.typedomain)

    def create_subtype_exclusion_propagation_axiom(self) \
            -> 'silver.ast.DomainAxiom':
        arg_sub = self.viper.LocalVarDecl('sub', self.typetype(),
                                          self.noposition(),
                                          self.noinfo())
        var_sub = self.viper.LocalVar('sub', self.typetype(),
                                      self.noposition(), self.noinfo())
        arg_middle = self.viper.LocalVarDecl('middle', self.typetype(),
                                             self.noposition(),
                                             self.noinfo())
        var_middle = self.viper.LocalVar('middle', self.typetype(),
                                         self.noposition(),
                                         self.noinfo())
        arg_super = self.viper.LocalVarDecl('super', self.typetype(),
                                            self.noposition(),
                                            self.noinfo())
        var_super = self.viper.LocalVar('super', self.typetype(),
                                        self.noposition(), self.noinfo())

        sub_middle = self.viper.DomainFuncApp('issubtype',
                                              [var_sub, var_middle], {},
                                              self.viper.Bool,
                                              [var_sub, var_middle],
                                              self.noposition(),
                                              self.noinfo(), self.typedomain)
        middle_super = self.viper.DomainFuncApp('isnotsubtype',
                                                [var_middle, var_super], {},
                                                self.viper.Bool,
                                                [var_middle, var_super],
                                                self.noposition(),
                                                self.noinfo(), self.typedomain)
        sub_super = self.viper.DomainFuncApp('issubtype', [var_sub, var_super],
                                             {}, self.viper.Bool,
                                             [var_sub, var_super],
                                             self.noposition(),
                                             self.noinfo(), self.typedomain)
        not_sub_super = self.viper.Not(sub_super, self.noposition(),
                                       self.noinfo())
        implication = self.viper.Implies(
            self.viper.And(sub_middle, middle_super, self.noposition(),
                           self.noinfo()), not_sub_super, self.noposition(),
            self.noinfo())
        trigger = self.viper.Trigger([sub_middle, middle_super], self.noposition(), self.noinfo())
        body = self.viper.Forall([arg_sub, arg_middle, arg_super], [trigger],
                                 implication, self.noposition(),
                                 self.noinfo())
        return self.viper.DomainAxiom('issubtype_exclusion_propagation', body,
                                      self.noposition(), self.noinfo(),
                                      self.typedomain)

    def create_null_type_axiom(self) -> 'silver.ast.DomainAxiom':
        null = self.viper.NullLit(self.noposition(), self.noinfo())
        type_func = self.viper.DomainFuncApp('typeof', [null], {},
                                             self.typetype(), [null],
                                             self.noposition(),
                                             self.noinfo(), self.typedomain)
        none_type = self.viper.DomainFuncApp('NoneType', [], {},
                                             self.typetype(), [],
                                             self.noposition(), self.noinfo(),
                                             self.typedomain)
        eq = self.viper.EqCmp(type_func, none_type, self.noposition(),
                              self.noinfo())
        return self.viper.DomainAxiom('null_nonetype', eq, self.noposition(),
                                      self.noinfo(), self.typedomain)

    def create_none_type_subtype_axiom(self) -> 'silver.ast.DomainAxiom':
        arg_sub = self.viper.LocalVarDecl('sub', self.typetype(),
                                          self.noposition(),
                                          self.noinfo())
        var_sub = self.viper.LocalVar('sub', self.typetype(),
                                      self.noposition(), self.noinfo())
        none_type = self.viper.DomainFuncApp('NoneType', [], {},
                                             self.typetype(), [],
                                             self.noposition(), self.noinfo(),
                                             self.typedomain)
        subtype = self.viper.DomainFuncApp('issubtype',
                                           [var_sub, none_type], {},
                                           self.viper.Bool,
                                           [var_sub, none_type],
                                           self.noposition(),
                                           self.noinfo(), self.typedomain)
        not_subtype = self.viper.Not(subtype, self.noposition(), self.noinfo())
        trigger = self.viper.Trigger([subtype], self.noposition(), self.noinfo())
        body = self.viper.Forall([arg_sub], [trigger],
                                 not_subtype, self.noposition(),
                                 self.noinfo())
        return self.viper.DomainAxiom('none_type_subtype', body,
                                      self.noposition(), self.noinfo(),
                                      self.typedomain)

    def create_object_type(self) -> 'silver.ast.DomainFunc':
        return self.create_type_function('object', self.noposition(),
                                         self.noinfo())

    def create_null_type(self) -> 'silver.ast.DomainFunc':
        return self.create_type_function('NoneType', self.noposition(),
                                         self.noinfo())

    def create_transitivity_axiom(self) -> 'silver.ast.DomainAxiom':
        """
        Creates the transitivity axiom for the PyType domain
        """
        arg_sub = self.viper.LocalVarDecl('sub', self.typetype(),
                                          self.noposition(),
                                          self.noinfo())
        var_sub = self.viper.LocalVar('sub', self.typetype(),
                                      self.noposition(), self.noinfo())
        arg_middle = self.viper.LocalVarDecl('middle', self.typetype(),
                                             self.noposition(),
                                             self.noinfo())
        var_middle = self.viper.LocalVar('middle', self.typetype(),
                                         self.noposition(),
                                         self.noinfo())
        arg_super = self.viper.LocalVarDecl('super', self.typetype(),
                                            self.noposition(),
                                            self.noinfo())
        var_super = self.viper.LocalVar('super', self.typetype(),
                                        self.noposition(), self.noinfo())

        sub_middle = self.viper.DomainFuncApp('issubtype',
                                              [var_sub, var_middle], {},
                                              self.viper.Bool,
                                              [var_sub, var_middle],
                                              self.noposition(),
                                              self.noinfo(), self.typedomain)
        middle_super = self.viper.DomainFuncApp('issubtype',
                                                [var_middle, var_super], {},
                                                self.viper.Bool,
                                                [var_middle, var_super],
                                                self.noposition(),
                                                self.noinfo(), self.typedomain)
        sub_super = self.viper.DomainFuncApp('issubtype', [var_sub, var_super],
                                             {}, self.viper.Bool,
                                             [var_sub, var_super],
                                             self.noposition(),
                                             self.noinfo(), self.typedomain)
        implication = self.viper.Implies(
            self.viper.And(sub_middle, middle_super, self.noposition(),
                           self.noinfo()), sub_super, self.noposition(),
            self.noinfo())
        trigger = self.viper.Trigger([sub_middle, middle_super],
                                     self.noposition(), self.noinfo())
        body = self.viper.Forall([arg_sub, arg_middle, arg_super], [trigger],
                                 implication, self.noposition(),
                                 self.noinfo())
        return self.viper.DomainAxiom('issubtype_transitivity', body,
                                      self.noposition(), self.noinfo(),
                                      self.typedomain)

    def create_reflexivity_axiom(self) -> 'silver.ast.DomainAxiom':
        """
        Creates the reflexivity axiom for the PyType domain
        """
        arg = self.viper.LocalVarDecl('type', self.typetype(),
                                      self.noposition(), self.noinfo())
        var = self.viper.LocalVar('type', self.typetype(),
                                  self.noposition(), self.noinfo())
        reflexive_subtype = self.viper.DomainFuncApp('issubtype', [var, var],
                                                     {}, self.viper.Bool,
                                                     [var, var],
                                                     self.noposition(),
                                                     self.noinfo(),
                                                     self.typedomain)
        trigger_exp = reflexive_subtype
        trigger = self.viper.Trigger([trigger_exp], self.noposition(),
                                     self.noinfo())
        body = self.viper.Forall([arg], [trigger], reflexive_subtype,
                                 self.noposition(), self.noinfo())
        return self.viper.DomainAxiom('issubtype_reflexivity', body,
                                      self.noposition(), self.noinfo(),
                                      self.typedomain)

    def typeof_func(self) -> 'silver.ast.DomainFunc':
        """
        Creates the typeof domain function
        """
        obj_var = self.viper.LocalVarDecl('obj', self.viper.Ref,
                                          self.noposition(),
                                          self.noinfo())
        return self.viper.DomainFunc('typeof', [obj_var],
                                     self.typetype(), False,
                                     self.noposition(), self.noinfo(),
                                     self.typedomain)

    def subtype_func(self, name: str) -> 'silver.ast.DomainFunc':
        """
        Creates the issubtype, extends and isnotsubtype domain functions.
        """
        sub_var = self.viper.LocalVarDecl('sub', self.typetype(),
                                          self.noposition(),
                                          self.noinfo())
        super_var = self.viper.LocalVarDecl('super', self.typetype(),
                                            self.noposition(),
                                            self.noinfo())
        return self.viper.DomainFunc(name, [sub_var, super_var],
                                     self.viper.Bool, False,
                                     self.noposition(), self.noinfo(),
                                     self.typedomain)

    def issubtype_func(self) -> 'silver.ast.DomainFunc':
        return self.subtype_func('issubtype')

    def isnotsubtype_func(self) -> 'silver.ast.DomainFunc':
        return self.subtype_func('isnotsubtype')

    def extends_func(self) -> 'silver.ast.DomainFunc':
        return self.subtype_func('extends_')

    def has_type(self, lhs: 'Expr', type: 'PythonClass'):
        """
        Creates an expression checking if the given lhs expression
        is of the given type
        """
        type_func = self.viper.DomainFuncApp('typeof', [lhs], {},
                                             self.typetype(), [lhs],
                                             self.noposition(),
                                             self.noinfo(), self.typedomain)
        supertype_func = self.viper.DomainFuncApp(type.sil_name, [], {},
                                                  self.typetype(), [],
                                                  self.noposition(),
                                                  self.noinfo(),
                                                  self.typedomain)
        var_sub = self.viper.LocalVar('sub', self.typetype(),
                                      self.noposition(), self.noinfo())
        var_super = self.viper.LocalVar('super', self.typetype(),
                                        self.noposition(), self.noinfo())
        subtype_func = self.viper.DomainFuncApp('issubtype',
                                                [type_func, supertype_func], {},
                                                self.viper.Bool,
                                                [var_sub, var_super],
                                                self.noposition(),
                                                self.noinfo(), self.typedomain)
        return subtype_func

    def has_concrete_type(self, lhs: 'Expr', type: 'PythonClass'):
        """
        Creates an expression checking if the given lhs expression
        is of the given type
        """
        type_func = self.viper.DomainFuncApp('typeof', [lhs], {},
                                             self.typetype(), [lhs],
                                             self.noposition(),
                                             self.noinfo(), self.typedomain)
        supertype_func = self.viper.DomainFuncApp(type.sil_name, [], {},
                                                  self.typetype(), [],
                                                  self.noposition(),
                                                  self.noinfo(),
                                                  self.typedomain)
        cmp = self.viper.EqCmp(type_func, supertype_func, self.noposition(),
                               self.noinfo())
        return cmp
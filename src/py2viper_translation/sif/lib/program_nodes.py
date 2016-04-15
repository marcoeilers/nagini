import ast

from py2viper_translation.lib.program_nodes import (
    PythonClass,
    PythonField,
    PythonScope,
    PythonVar,
    ProgramNodeFactory,
)
from py2viper_translation.translator import Translator
from typing import List


SIF_VAR_SUFFIX = "_p"


class SIFPythonClass(PythonClass):
    def get_all_fields(self) -> List['SIFPythonField']:
        fields = []
        cls = self
        while cls is not None:
            for field in cls.fields.values():
                if field.inherited is None:
                    fields.append(field)
            cls = cls.superclass

        return fields

    def get_all_sil_fields(self) -> List['silver.ast.Field']:
        fields = []
        cls = self
        while cls is not None:
            for field in cls.fields.values():
                if field.inherited is None:
                    fields.append(field.sil_field)
            cls = cls.superclass

        return fields


class SIFPythonVar(PythonVar):
    """
    SIF version of a PythonVar. Has a reference to the corresponding ghost var.
    """
    def __init__(self, name: str, node: ast.AST, type_: SIFPythonClass):
        super().__init__(name, node, type_)
        self.var_prime = PythonVar(name + SIF_VAR_SUFFIX, node, type_)

    def process(self, sil_name: str, translator: Translator):
        super().process(sil_name, translator)
        self.var_prime.process(sil_name + SIF_VAR_SUFFIX, translator)


class SIFPythonField(PythonField):
    """
    SIF version of a PythonField. Has a reference to the corresponding ghost
    field.
    """
    def __init__(self, name: str, node: ast.AST, type_: PythonClass,
                 cls: PythonClass):
        super().__init__(name, node, type_, cls)
        self.field_prime = PythonField(name + SIF_VAR_SUFFIX,
                                       node, type_, cls)

    def process(self, sil_name: str):
        super().process(sil_name)
        self.field_prime.process(sil_name + SIF_VAR_SUFFIX)

    def _set_sil_field(self, field: 'silver.ast.Field'):
        super()._set_sil_field(field)
        # Make a Silver-AST copy.
        sil_field = field.copy(self.field_prime.sil_name,
                               field.typ(), field.pos(), field.info())
        self.field_prime.sil_field = sil_field


class SIFProgramNodeFactory(ProgramNodeFactory):
    def create_python_var(self, name: str, node: ast.AST,
                          type_: PythonClass) -> SIFPythonVar:
        return SIFPythonVar(name, node, type_)

    def create_python_field(self, name: str, node: ast.AST, type_: PythonClass,
                            cls: PythonClass):
        return SIFPythonField(name, node, type_, cls)

    def create_python_class(self, name: str, superscope: PythonScope,
                            node_factory: 'SIFProgramNodeFactory',
                            node: ast.AST = None,
                            superclass: SIFPythonClass = None,
                            interface=False):
        return SIFPythonClass(name, superscope, node_factory, node,
                              superclass, interface)

import ast

from py2viper_translation.lib.program_nodes import (
    PythonClass,
    PythonField,
    PythonMethod,
    PythonScope,
    PythonVar,
    ProgramNodeFactory,
)
from py2viper_translation.translator import Translator
from typing import List


SIF_VAR_SUFFIX = "_p"


class SIFPythonMethod(PythonMethod):
    """
    SIF version of a PythonMethod.
    """
    def __init__(self, name: str, node: ast.AST, cls: PythonClass,
                 superscope: PythonScope,
                 pure: bool, contract_only: bool,
                 node_factory: 'ProgramNodeFactory',
                 interface: bool = False):
        super().__init__(name, node, cls, superscope, pure, contract_only,
                         node_factory, interface)
        bool_type = cls.get_program().classes['bool']
        self.tl_var = PythonVar("timeLevel", None, bool_type)
        self.new_tl_var = PythonVar("newTimeLevel", None, bool_type)

    def process(self, sil_name: str, translator: 'Translator'):
        super().process(sil_name, translator)
        self.tl_var.process(self.tl_var.name, translator)
        self.new_tl_var.process(self.new_tl_var.name, translator)

    def get_locals(self) -> List['PythonVar']:
        """
        Returns all method locals as a list of PythonVars.
        """
        locals = []
        for local in self.locals.values():
            locals.append(local)
            locals.append(local.var_prime)

        return locals

    def get_args(self) -> List['PythonVar']:
        """
        Returns all method args as a list of PythonVars.
        """
        args = []
        for arg in self.args.values():
            args.append(arg)
            args.append(arg.var_prime)
        # Add timeLevel.
        args.append(self.tl_var)
        return args

    def get_results(self) -> List['PythonVar']:
        """
        Returns all results as a list of PythonVars.
        """
        results = []
        if self.result:
            results.append(self.result)
            results.append(self.result.var_prime)
        # Add newTimeLevel.
        results.append(self.new_tl_var)
        return results


class SIFPythonVar(PythonVar):
    """
    SIF version of a PythonVar. Has a reference to the corresponding ghost var.
    """
    def __init__(self, name: str, node: ast.AST, type_: PythonClass):
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

    def create_python_method(self, name: str, node: ast.AST, cls: PythonClass,
                             superscope: PythonScope,
                             pure: bool, contract_only: bool,
                             container_factory: 'ProgramNodeFactory',
                             interface: bool = False) -> SIFPythonMethod:
        return SIFPythonMethod(name, node, cls, superscope, pure, contract_only,
                               container_factory, interface)

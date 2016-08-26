import ast

from py2viper_translation.lib.constants import BOOL_TYPE
from py2viper_translation.lib.program_nodes import (
    PythonClass,
    PythonField,
    PythonMethod,
    PythonScope,
    PythonVar,
    ProgramNodeFactory,
)
from py2viper_translation.sif.lib.constants import (
    NEW_TL_VAR_NAME,
    SIF_VAR_SUFFIX,
    TL_VAR_NAME,
)
from py2viper_translation.translator import Translator
from typing import List


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
        bool_type = superscope.get_program().global_prog.classes[BOOL_TYPE]
        self.tl_var = PythonVar(TL_VAR_NAME, None, bool_type)
        self.new_tl_var = PythonVar(NEW_TL_VAR_NAME, None, bool_type)
        self._set_preserves_tl()

    @property
    def preserves_tl(self) -> bool:
        return self._preserves_tl

    def _set_preserves_tl(self):
        # FIXME(shitz): This should actually be done in the Analyzer, however,
        # then I'd need to subclass it, which I think is not reasonable just
        # for this single case. If the need for a custom analyzer increases
        # we can move this there eventually.
        decorators = {d.id for d in self.node.decorator_list}
        self._preserves_tl = 'NotPreservingTL' not in decorators

    def process(self, sil_name: str, translator: 'Translator'):
        super().process(sil_name, translator)
        self.tl_var.process(self.tl_var.name, translator)
        self.new_tl_var.process(self.new_tl_var.name, translator)

    def get_variable(self, name: str) -> 'SIFPythonVar':
        if name == self.tl_var.name:
            return self.tl_var
        elif name == self.new_tl_var.name:
            return self.new_tl_var
        else:
            return super().get_variable(name)

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
        if name.startswith(TL_VAR_NAME) or name.startswith(NEW_TL_VAR_NAME):
            self.var_prime = self
        else:
            self.var_prime = PythonVar(name + SIF_VAR_SUFFIX, node, type_)

    def process(self, sil_name: str, translator: Translator):
        super().process(sil_name, translator)
        if self.var_prime != self:
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

from py2viper_translation.analyzer import Analyzer
from py2viper_translation.lib.program_nodes import (
    ProgramNodeFactory,
    TypeVar,
)
from py2viper_translation.sif.lib.program_nodes import SIFProgramNodeFactory
from typing import Dict


class SIFAnalyzer(Analyzer):
    """SIF version of the Analyzer."""

    @property
    def node_factory(self):
        if not self._node_factory:
            self._node_factory = SIFProgramNodeFactory()
        return self._node_factory

    def add_native_silver_builtins(self, interface: Dict) -> None:
        # Create global classes first
        for class_name in interface:
            cls = self.find_or_create_class(class_name,
                                            module=self.module.global_module)
            cls.interface = True
            cls.defined = True
        for class_name in interface:
            cls = self.find_or_create_class(class_name)
            if_cls = interface[class_name]
            if if_cls.get("generate_sif", False):
                node_factory = SIFProgramNodeFactory()
            else:
                node_factory = ProgramNodeFactory()

            if 'type_vars' in if_cls:
                for i in range(if_cls['type_vars']):
                    name = 'var' + str(i)
                    cls.type_vars[name] = TypeVar(name, cls, None, i, None, [],
                                                  None)
            if 'extends' in if_cls:
                superclass = self.find_or_create_class(
                    if_cls['extends'], module=self.module.global_module)
                cls.superclass = superclass
            for method_name in if_cls.get('methods', []):
                if_method = if_cls['methods'][method_name]
                self._add_native_silver_method(method_name, if_method, cls,
                                               False, node_factory=node_factory)
            for method_name in if_cls.get('functions', []):
                if_method = if_cls['functions'][method_name]
                self._add_native_silver_method(method_name, if_method, cls,
                                               True, node_factory=node_factory)
            for pred_name in if_cls.get('predicates', []):
                if_pred = if_cls['predicates'][pred_name]
                self._add_native_silver_method(pred_name, if_pred, cls, True,
                                               True, node_factory=node_factory)

from nagini_translation.analyzer import Analyzer
from nagini_translation.lib.program_nodes import ProgramNodeFactory
from nagini_translation.sif.lib.program_nodes import SIFProgramNodeFactory
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
            if_cls = interface[class_name]
            if if_cls.get("generate_sif", False):
                node_factory = SIFProgramNodeFactory()
            else:
                node_factory = ProgramNodeFactory()
            self._process_interface_class(class_name, if_cls, node_factory)

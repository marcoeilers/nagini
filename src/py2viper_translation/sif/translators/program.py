from py2viper_translation.lib.program_nodes import PythonClass
from py2viper_translation.sif.lib.context import SIFContext
from py2viper_translation.translators.program import ProgramTranslator
from typing import List


class SIFProgramTranslator(ProgramTranslator):
    """
    SIF version of the ProgramTranslator.
    """
    def _translate_fields(self, cls: PythonClass,
                          ctx: SIFContext) -> List['silver.ast.Field']:
        fields = []
        for field in cls.fields.values():
            if field.inherited is None:
                sil_field = self.translate_field(field, ctx)
                field.sil_field = sil_field
                fields.append(sil_field)
                sil_field_p = self.translate_field(field.field_prime, ctx)
                field.field_prime.sil_field = sil_field_p
                fields.append(sil_field_p)

        return fields

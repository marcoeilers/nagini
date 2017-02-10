from py2viper_translation.lib.program_nodes import PythonClass
from py2viper_translation.lib.typedefs import Field
from py2viper_translation.sif.lib.context import SIFContext
from py2viper_translation.translators.program import ProgramTranslator
from typing import List


class SIFProgramTranslator(ProgramTranslator):
    """
    SIF version of the ProgramTranslator.
    """
    def _create_predefined_fields(self, ctx: SIFContext) -> List[Field]:
        """
        Creates and returns fields needed for encoding various language
        features, e.g. collections, measures and iterators.
        """
        fields = super()._create_predefined_fields(ctx)
        fields.append(self.viper.Field('list_acc_p',
                                       self.viper.SeqType(self.viper.Ref),
                                       self.no_position(ctx),
                                       self.no_info(ctx)))
        return fields

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

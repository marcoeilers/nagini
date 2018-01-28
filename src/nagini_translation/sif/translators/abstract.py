"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

from nagini_translation.translators.abstract import TranslatorConfig


class SIFTranslatorConfig(TranslatorConfig):
    """
    SIF version of the TranslatorConfig.
    """
    def __init__(self, translator: 'Translator'):
        super().__init__(translator)
        self.func_triple_factory = None

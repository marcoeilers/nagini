# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from resources.pkg_relative import Holder


# Holder is only reachable through the relative import in the package's
# __init__.py. Its module used to keep its cached, stripped mypy AST, so no
# types were collected for it at all and this failed to translate (issue #284).
def use_reexported(h: Holder) -> bool:
    Requires(h.value > 4)
    return True

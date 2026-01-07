# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

from resources.import_for_00266 import foo

class client():
    def client_test(self) -> None:
        instance = foo.bar()
        assert instance.value
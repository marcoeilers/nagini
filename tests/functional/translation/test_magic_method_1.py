# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

class TestClass:

    #:: ExpectedOutput(invalid.program:illegal.magic.method)
    def __getattr__(self, item: str) -> object:
        return None

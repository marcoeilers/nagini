class TestClass:

    #:: ExpectedOutput(invalid.program:illegal.magic.method)
    def __getattr__(self, item: str) -> object:
        return None

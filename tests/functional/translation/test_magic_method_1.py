class TestClass:

    #:: ExpectedOutput(invalid.program:illegal.magic.method)
    def __getitem__(self, item: str) -> object:
        pass
def test() -> None:
    #:: ExpectedOutput(type.error:Name 'foo' is not defined)
    foo()  # noqa: F821

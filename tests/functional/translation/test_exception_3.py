def test() -> None:
    try:
        raise Exception()
        #:: ExpectedOutput(type.error:dead.code)
        a = 2
    except Exception as ex:
        pass

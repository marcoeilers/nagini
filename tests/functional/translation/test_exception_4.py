def test() -> None:
    try:
        raise Exception()
    except Exception as ex:
        raise Exception()
        #:: ExpectedOutput(type.error:dead.code)
        a = 2

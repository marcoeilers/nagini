def test() -> None:
    try:
        raise Exception()
    finally:
        raise Exception()
        #:: ExpectedOutput(type.error:dead.code)
        a = 2

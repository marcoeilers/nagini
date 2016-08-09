#:: IgnoreFile(/py2viper/issue/54/)


def foo() -> int:
    return 1


def test() -> None:
    try:
        x = foo()
    except:
        pass

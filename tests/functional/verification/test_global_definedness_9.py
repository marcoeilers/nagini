b_bar = 12


def baz(b: object = b_bar) -> int:
    return 12


#:: ExpectedOutput(expression.undefined:undefined.global.name)|MissingOutput(expression.undefined:undefined.global.name, 95)
def foo(a: object = a_bar) -> int:  # noqa: F821
    return 12

a_bar = 12
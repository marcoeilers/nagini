a_bar = 12


class C:
    baz = a_bar


class D:
    #:: ExpectedOutput(expression.undefined:undefined.global.name)
    baz = b_bar

b_bar = 12
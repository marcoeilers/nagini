from contracts import *

@Pure
def func1() -> int:
    Ensures(Result() == 16)
    return  16
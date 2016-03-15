from contracts.contracts import *

@Pure
def double(input: int) -> int:
    Ensures(Result() == 2 * input)
    return 2 * input
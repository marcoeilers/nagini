
def from_type() -> None:
    #:: ExpectedOutput(type.error:Exception must be derived from BaseException)
    raise Exception() from 2
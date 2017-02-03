def m() -> None:
    a = (1,2,3,4,5,6)
    #:: ExpectedOutput(type.error:Two starred expressions in assignment)
    b, *c, *d = a
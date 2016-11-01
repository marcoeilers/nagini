from py2viper_contracts.contracts import *


class A:
    some_field = "Afield"


class B(A):
    #:: ExpectedOutput(invalid.program:invalid.override)
    some_field = "Bfield"

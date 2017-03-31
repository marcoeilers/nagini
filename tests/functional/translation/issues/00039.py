#:: IgnoreFile(39)
from nagini_contracts.contracts import *


@Pure
@ContractOnly  #:: ExpectedOutput(type.error:Encountered Any type. Type annotation missing?)
def read_int_io():
    pass

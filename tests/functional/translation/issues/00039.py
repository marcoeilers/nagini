#:: IgnoreFile(/py2viper/issue/39/)
from py2viper_contracts.contracts import *


@Pure
@ContractOnly  #:: ExpectedOutput(type.error:Encountered Any type. Type annotation missing?)
def read_int_io():
    pass

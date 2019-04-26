# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

#:: IgnoreFile(39)
from nagini_contracts.contracts import *


@Pure
@ContractOnly  #:: ExpectedOutput(type.error:Encountered Any type. Type annotation missing?)
def read_int_io():
    pass

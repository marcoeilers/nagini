from py2viper_contracts.contracts import *


class Super:
    pass

def test_constr() -> None:
    super1 = Super()
    super2 = Super()
    super3 = Super()
    mydict = {1: super1, 7 : super3}
    empty_dict = {} # type: Dict[int, Super]

def test_in() -> None:
    super1 = Super()
    super2 = Super()
    super3 = Super()
    mydict = {1: super1, 7 : super3}
    empty_dict = {} # type: Dict[int, Super]
    Assert(1 in mydict)
    Assert(not (1 in empty_dict))
    Assert(7 in mydict)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(4 in mydict)

def test_subscript() -> None:
    super1 = Super()
    super2 = Super()
    super3 = Super()
    mydict = {1: super1, 7 : super3}
    empty_dict = {} # type: Dict[int, Super]
    Assert(mydict[1] == super1)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(mydict[7] == super2)

def test_get() -> None:
    super1 = Super()
    super2 = Super()
    super3 = Super()
    mydict = {1: super1, 7 : super3}
    empty_dict = {} # type: Dict[int, Super]
    Assert(mydict.get(1) == super1)
    Assert(mydict.get(7) == super3)
    Assert(mydict.get(44) == None)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(empty_dict.get(45) == super2)

def test_set() -> None:
    super1 = Super()
    super2 = Super()
    super3 = Super()
    mydict = {1: super1, 7 : super3}
    empty_dict = {} # type: Dict[int, Super]
    Assert(not (4 in empty_dict))
    empty_dict[4] = super2
    Assert(4 in empty_dict)
    Assert(empty_dict[4] == super2)
    Assert(mydict[1] == super1)
    Assert(not (1 in empty_dict))
    mydict[1] = super3
    Assert(mydict[1] == super3)
    Assert(1 in mydict)
    Assert(mydict[7] == super3)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(mydict[1] == super1)
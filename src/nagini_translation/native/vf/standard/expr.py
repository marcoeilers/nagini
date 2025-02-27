from abc import ABC
from nagini_translation.native.vf.standard.value import Value
from nagini_translation.native.vf.standard.literal import Int, Bool
from nagini_translation.native.vf.standard.inductive import Inductive
from typing import Generic, TypeVar
_BoolT = TypeVar("ValueT", bound="Bool")
_ValueT = TypeVar("ValueT", bound="Value")
_ValueT2 = TypeVar("ValueT2", bound="Value")
_ValueT3 = TypeVar("ValueT3", bound="Value")


class Expr(ABC, Generic[_ValueT]):
    # any expression must return a value in the end...
    def __init__(self, value: _ValueT):
        self.__value = value

    def __str__(self) -> str:
        return str(self.__value)


class NameOccurence(ABC):
    def __init__(self, entity: "NamedValue"):
        self.__entity = entity

    def __str__(self) -> str:
        return str(self.__entity)


class NameDefExpr(Expr[_ValueT], NameOccurence):
    def __init__(self, entity: "NamedValue[_ValueT]"):
        NameOccurence.__init__(self, entity)

    def __str__(self) -> str:
        return "?" + NameOccurence.__str__(self)


class NamedValue(Generic[_ValueT]):
    def __init__(self,  name: str):
        self.__def = None
        self.__name = name

    def getName(self):
        return self.__name

    def setDef(self, defn: NameDefExpr):
        self.__def = defn

    def getDef(self) -> NameDefExpr:
        return self.__def

    def __str__(self) -> str:
        return self.__name


class DefLessExpr(Expr[_ValueT], ABC):
    # definitionless expression: only uses names, no definitions
    pass


class NameUseExpr(NameOccurence, DefLessExpr[_ValueT]):
    def __init__(self, entity):
        NameOccurence.__init__(self, entity)

    def __str__(self):
        return NameOccurence.__str__(self)


class ImmLiteral(DefLessExpr[_ValueT]):
    pass


_InductiveT = TypeVar("InductiveT", bound="Inductive")


class ImmInductive(Expr[_InductiveT]):
    def __str__(self):
        return super().__str__()


class BinaryOperator(ABC, Generic[_ValueT, _ValueT2]):
    def __init__(self, symbol: str):
        self.symbol = symbol

    def __str__(self):
        return self.symbol


Add = BinaryOperator[Int, Int]("+")
Sub = BinaryOperator[Int, Int]("-")
Mul = BinaryOperator[Int, Int]("*")
Div = BinaryOperator[Int, Int]("/")
Mod = BinaryOperator[Int, Int]("%")
BitAnd = BinaryOperator[Int, Int]("&")
BitOr = BinaryOperator[Int, Int]("|")
BitXor = BinaryOperator[Int, Int]("^")
LShift = BinaryOperator[Int, Int]("<<")
RShift = BinaryOperator[Int, Int](">>")
Lt = BinaryOperator[Int, Bool]("<")
LtE = BinaryOperator[Int, Bool]("<=")
Gt = BinaryOperator[Int, Bool](">")
GtE = BinaryOperator[Int, Bool](">=")
Eq = BinaryOperator[Int, Bool]("==")
NotEq = BinaryOperator[Int, Bool]("!=")
BoolAnd = BinaryOperator[Bool, Bool]("&&")
BoolOr = BinaryOperator[Bool, Bool]("||")


class BinOp(Expr[_ValueT]):
    # _ValueT = TypeVar("ValueT", bound="Value")
    # _ValueT2 = TypeVar("ValueT2", bound="Value")
    def __init__(self, left: Expr[_ValueT2], right: Expr[_ValueT2], op: BinaryOperator[_ValueT2, _ValueT]):
        self.left = left
        self.right = right
        self.op = op

    def __str__(self):
        return "("+str(self.left)+" "+str(self.op)+" "+str(self.right)+")"


class TernaryOp(DefLessExpr[_ValueT], ABC):
    def __init__(self, cond: Expr[_BoolT], left: Expr[_ValueT], right: Expr[_ValueT]):
        self.cond = cond
        self.left = left
        self.right = right

    def __str__(self):
        return "("+str(self.cond)+" ? "+str(self.left)+" : "+str(self.right)+")"

from abc import ABC
from typing import Generic, TypeVar
from nagini_translation.native.vf.standard.value import Value
from nagini_translation.native.vf.standard.expr import Expr

ExprT = TypeVar("ExprT", bound="Expr")


class Inductive(Value, ABC, Generic[ExprT]):
    pass

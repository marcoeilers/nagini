from typing import *

from nagini_contracts.contracts import *

Shape = Tuple[int, ...]

class ndarray:
  @property
  def shape(self) -> Shape:
    ...

  @shape.setter
  def shape(self, new_shape: Shape) -> None:
    ...


@Predicate
@ContractOnly
def array_pred(array: ndarray) -> bool:
  return True


@Pure
@ContractOnly
def array_shape(array: ndarray) -> Shape: #type: ignore[return]
  Requires(Acc(array_pred(array), 1/2))
  ...

@ContractOnly
def ones(shape: Shape) -> ndarray: #type: ignore[return]
  Requires(len(shape) > 0)
  Requires(Forall(shape, lambda l: l > 0))

  Ensures(array_pred(Result()))
  Ensures(array_shape(Result()) == shape)
  ...

shape = (2,)
array1 = ones(shape)
array2 = ones(shape)



assert array_shape(array1) == shape
assert array_shape(array2) == shape
assert array_shape(array1) == array_shape(array2)
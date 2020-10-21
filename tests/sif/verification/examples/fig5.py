from nagini_contracts.contracts import *

def _print(b: bool) -> None:
    Requires(Low(b))

def get_object(o: object, v: int) -> object:
  Ensures((Result() is not o) if v > 0 else (Result() is o))
  if v > 0:
    return object()
  return o

def main(v: int) -> None:
  o1 = object()
  o2 = get_object(o1, v)
  _print(o1 is o2)

def main_correct(v: int) -> None:
  Requires(Low(v > 0))
  o1 = object()
  o2 = get_object(o1, v)
  _print(o1 is o2)
from typing import Union


def print(msg: str) -> None:
    pass


class Parrot:
    def fly(self) -> None:
        print("Parrot flying")


class Airplane:
    def fly(self) -> None:
        print("Airplane flying")


class Whale:
    def swim(self) -> None:
        print("Whale swimming")


def lift_off(entity: Union[Parrot, Airplane]) -> None:
    entity.fly()

parrot = Parrot()
airplane = Airplane()
whale = Whale()

lift_off(parrot) # prints `Parrot flying`
lift_off(airplane) # prints `Airplane flying`
# lift_off(whale) # Throws the error `'Whale' object has no attribute 'fly'`
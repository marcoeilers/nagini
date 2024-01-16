class Parent:
    def __getattr__(self, name: str) -> str:
        return "foo"

class Subclass(Parent):
    def __setattr__(self, name: str, value: int) -> None:
        self.__dict__[name] = str(value) + "foo"


instance = Subclass()

print(instance.hello + "bar")
instance.hello = 100
print(instance.hello + "bar")


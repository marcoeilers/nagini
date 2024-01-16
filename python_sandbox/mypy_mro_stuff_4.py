
class Parent:
    def __getattr__(self, name: str) -> str:
        return "foo"

class Subclass(Parent):
    def __init__(self, set_x: bool) -> None:
        if set_x:
            self.x = 100


instance_with_x = Subclass(True)
instance_without_x = Subclass(False)

print(instance_with_x.x + 10)
getattr(instance_without_x, "x") + 15
# print(instance_without_x.x + "bar")   # error: Unsupported operand types for + ("int" and "str")
print(instance_without_x.y + "bar")


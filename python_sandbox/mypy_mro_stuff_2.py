class Parent:
    x = 15
    
    
class Subclass(Parent):
    def __getattr__(self, name: str) -> str:
        return "foo"

def needs_str(var: str) -> bool:
    return type(var) == str

def needs_int(var: int) -> bool:
    return type(var) == int   


instance = Subclass()
print(instance.hello + "bar")
print(instance.x + 10)
print(needs_str(instance.hello))
print(needs_int(instance.x))

instance.__dict__['hello'] = 100
# instance.hello = 100            # error: "Subclass" has no attribute "hello"
# Subclass.hello = 100            # error: "Type[Subclass]" has no attribute "hello"
print(instance.hello + 50)        # Unsupported operand types for + ("str" and "int")
print(needs_int(instance.hello))  # Argument 1 to "needs_int" has incompatible type "str"; expected "int"


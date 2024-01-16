class Parent:
    def __getattr__(self, name: str) -> str:
        return "foo"
    
    
class Subclass(Parent):
    x = 100

def some_func(instance: Parent) -> str:
    return instance.x + "bar"     # should have an error here, but does not


instance = Subclass()

print(some_func(instance))


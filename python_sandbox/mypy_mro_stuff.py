class Grandparent:
    x = "abcd"
    def __getattr__(self, name: str) -> str:
        return "foobar"
    
    def __init__(self) -> None:
        self.instance_attr = "hello_world"

class Parent(Grandparent):
    # Incompatible types in assignment (expression has type "int", base class "Grandparent" defined the type as "str")
    x = 15
    
    # Return type "int" of "__getattr__" incompatible with return type "str" in supertype "Grandparent"
    def __getattr__(self, name: str) -> int:
        return 25
    
    def __init__(self) -> None:
        # Incompatible types in assignment (expression has type "int", variable has type "str")
        self.instance_attr = 70
    
class Subclass(Parent):
    pass
    
def some_func(instance: Grandparent) -> str:
    return instance.x + "asd"



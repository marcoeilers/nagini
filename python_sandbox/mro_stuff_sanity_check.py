from typing import Any, Dict, Tuple

# class Parent_with_class_and_instance_x:
#     x = 100
#     def __init__(self) -> None:
#         self.x = 10
    
class Parent_with_class_x:
    x = 100
    y = 300
    
# class Parent_with_instance_x:
#     def __init__(self) -> None:
#         self.x = 10
        
# class Subclass_with_class_and_instance_x(Parent_with_class_and_instance_x):
#     x = 200
#     def __init__(self) -> None:
#         self.x = 20

# class Subclass_with_class_x(Parent_with_class_and_instance_x):
#     x = 200
        
class Subclass_with_instance_x(Parent_with_class_x):
    def __init__(self) -> None:
        self.x = 20
        
    def __getattr__(self, name):
        return 800

instance = Subclass_with_instance_x()
print(instance.x)
print(type(instance).x)
print(type(instance).__bases__[0].x)


print(instance.y)

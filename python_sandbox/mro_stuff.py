from typing import Any, Dict, Tuple

class Parent_with_class_and_instance_x:
    x = "parent_class"
    def __init__(self) -> None:
        self.x = "parent_instance"
    
class Parent_with_class_x:
    x = "parent_class"
    
class Parent_with_instance_x:
    def __init__(self) -> None:
        self.x = "parent_instance"

class Parent_with_nothing:
    pass

class Subclass_with_class_and_instance_x:
    x = "subclass_class"
    def __init__(self) -> None:
        self.x = "subclass_instance"

class Subclass_with_class_x:
    x = "subclass_class"
        
class Subclass_with_instance_x:
    def __init__(self) -> None:
        self.x = "subclass_instance"

class Subclass_with_nothing:
    pass


parents = [Parent_with_class_and_instance_x, Parent_with_class_x, Parent_with_instance_x, Parent_with_nothing]
subclasses = [Subclass_with_class_and_instance_x, Subclass_with_class_x, Subclass_with_instance_x, Subclass_with_nothing]

combinations = []
for parent in parents:
    for subclass in subclasses:
        combinations.append(type(
            parent.__name__ + " " + subclass.__name__,
            (parent,),
            {key: subclass.__dict__[key] for key in subclass.__dict__ if key in ["x", "__init__"]}
        ))

for combination in combinations:
    print(combination.__name__)
    instance = combination()
    try:
        instance_x = instance.x
    except AttributeError:
        instance_x = "Not Found"
    
    try:
        subclass_x = type(instance).x
    except AttributeError:
        subclass_x = "Not Found"
        
    try:
        parent_x = type(instance).__bases__[0].x
    except AttributeError:
        parent_x = "Not Found"
    
    print(f"instance.x: {instance_x}")
    print(f"subclass.x: {subclass_x}")
    print(f"parent.x: {parent_x}")
    print()

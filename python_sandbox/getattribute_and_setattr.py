class Empty:
    pass

class Dynamic:
    def __getattr__(self, name):
        return "bar"

    def my_func(self):
        return "my_func_return"

    def __getattribute__(self, name):
        print(f"__getattribute__({name})")
        if name == "__dict__" or name == "x" or name == "foo" or name == "my_func":
            # for foo this actually works because AttributeError here will call __getattr__
            return object.__getattribute__(self, name)
        elif name == "attr_error_elsewhere":
            e = Empty()
            return object.__getattribute__(e, name)
        else:
            return "world"

    def __setattr__(self, name, value):
        print(f"__setattr__({name}, {value})")
        # print(f"object.__getattribute__(self, name) = {object.__getattribute__(self, name)}")
        self.__dict__[name] = value + 1


d = Dynamic()
print("d.x = 10")
d.x = 10

print()
print()

print("d.x")
print(d.x)

print()
print()

print("d.foo")
print(d.foo)

print()
print()

print("d.hello")
print(d.hello)

print()
print()

print("d.my_func()")
print(d.my_func())

print()
print()

# this doesn't work because object.__getattribute__ outside of a __getattribute__ doesn't call __getattr__
# print('object.__getattribute__(d, "hello")')
# print(object.__getattribute__(d, "hello"))

print()
print()

print('d.attr_error_elsewhere')
print(d.attr_error_elsewhere)

print()
print()

print('getattr(d, "hello")')
print(getattr(d, "hello"))

print()
print()

print('getattr(d, "foo")')
print(getattr(d, "foo"))

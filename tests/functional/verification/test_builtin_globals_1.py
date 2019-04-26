# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

fl = __file__
assert __name__ == '__main__'

assert fl == __file__

#:: ExpectedOutput(assignment.failed:insufficient.permission)
__file__ = "asd"
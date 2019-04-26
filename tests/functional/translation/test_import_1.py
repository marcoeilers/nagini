# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

def does_import() -> int:
    #:: ExpectedOutput(invalid.program:local.import)
    import resources.test_import_1_file
    return 12
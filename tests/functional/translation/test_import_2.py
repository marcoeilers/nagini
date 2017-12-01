def does_import() -> int:
    #:: ExpectedOutput(invalid.program:local.import)
    from resources.test_import_1_file import *
    return 12
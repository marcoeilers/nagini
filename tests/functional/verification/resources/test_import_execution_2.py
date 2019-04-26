# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

import resources.test_import_execution_1

wow = 23


import test_import_execution

assert test_import_execution.a == 2

test_import_execution.a += 1
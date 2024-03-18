#!/bin/bash

#nagini --verifier silicon --write-viper-to-file iap_bst.vpr tests/functional/verification/examples/iap_bst.py
if [ "$1" = "run_all_tests" ]; then
  pytest src/nagini_translation/tests.py
elif [ "$1" = "nothing" ]; then
  echo "shutdown"
elif [ "$1" = "silicon" ]; then
  pytest src/nagini_translation/tests.py --silicon --single-test "$1"
elif [ "$1" = "carbon" ]; then
  pytest src/nagini_translation/tests.py --carbon --single-test "$1"
else
  pytest src/nagini_translation/tests.py --carbon --single-test "$1"
fi
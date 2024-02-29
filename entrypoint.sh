#!/bin/bash

#nagini --verifier silicon --write-viper-to-file iap_bst.vpr tests/functional/verification/examples/iap_bst.py
if [ "$1" = "run_all_tests" ]; then
  pytest src/nagini_translation/tests.py --carbon
elif [ "$1" = "nothing" ]; then
  echo "shutdown"
else
  pytest src/nagini_translation/tests.py --carbon --single-test "$1"
fi
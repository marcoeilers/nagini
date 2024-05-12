#!/bin/bash

#nagini --verifier silicon --write-viper-to-file iap_bst.vpr tests/functional/verification/examples/iap_bst.py
if [ "$1" = "run_all_tests" ]; then
  pytest src/nagini_translation/tests.py
elif [ "$1" = "nothing" ]; then
  echo "shutdown"
elif [ "$1" = "silicon" ]; then
  pytest src/nagini_translation/tests.py --silicon --single-test "$2"
elif [ "$1" = "carbon" ]; then
  pytest src/nagini_translation/tests.py --carbon --single-test "$2"
elif [ "$1" = "evaluate_file" ]; then
  python src/nagini_translation/main.py --verifier "$2" --write-viper-to-file file.vpr "$3"
  wc -l file.vpr
else
  pytest src/nagini_translation/tests.py --carbon --single-test "$2"
fi
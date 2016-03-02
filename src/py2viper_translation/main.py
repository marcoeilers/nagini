import ast
import os
import sys
import argparse

from py2viper_translation import astpp
from py2viper_translation import config
from py2viper_translation.analyzer import Analyzer
from jpype import JavaException
from py2viper_translation.jvmaccess import JVM
from os.path import expanduser
from py2viper_translation.translator import Translator, InvalidProgramException
from py2viper_translation.typeinfo import TypeInfo, TypeException
from py2viper_translation.verifier import (
    Carbon,
    Silicon,
    VerificationResult,
    ViperVerifier)
from py2viper_translation.viper_ast import ViperAST


def translate(path: str, jvm: JVM):
    """
    Translates the Python module at the given path to a Viper program
    """
    types = TypeInfo()
    typecorrect = types.check(path)
    try:
        if typecorrect:
            with open(path, 'r') as file:
                text = file.read()
            parseresult = ast.parse(text)
            viperast = ViperAST(jvm, jvm.java, jvm.scala, jvm.viper, path)
            translator = Translator(jvm, path, types, viperast)
            analyzer = Analyzer(jvm, viperast, types)
            analyzer.visit_default(parseresult)
            analyzer.process(translator)
            prog = translator.translate_program(analyzer.program)
            return prog
        else:
            return None
    except JavaException as je:
        print(je.stacktrace())


def verify(prog: 'viper.silver.ast.Program', path: str,
           jvm: JVM, backend=ViperVerifier.silicon) -> VerificationResult:
    """
    Verifies the given Viper program
    """
    try:
        if backend == ViperVerifier.silicon:
            verifier = Silicon(jvm, path)
        elif backend == ViperVerifier.carbon:
            verifier = Carbon(jvm, path)
        vresult = verifier.verify(prog)
        return vresult
    except JavaException as je:
        print(je.stacktrace())


def main() -> None:
    """ Entry point for the translator.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'python_file',
        help='Python file to verify')
    parser.add_argument(
        '--viper-jar-path',
        help='Java CLASSPATH that includes Viper class files',
        default=config.classpath)
    parser.add_argument(
        '--boogie',
        help='path to Boogie executable',
        default=config.boogie_path)
    parser.add_argument(
        '--z3',
        help='path to Z3 executable',
        default=config.z3_path)
    parser.add_argument(
        '--mypy-path',
        help='mypy path',
        default=config.mypy_path)
    parser.add_argument(
        '--print-silver',
        action='store_true',
        help='print generated Silver program')
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="increase output verbosity")
    args = parser.parse_args()

    python_file = args.python_file
    config.classpath = args.viper_jar_path
    config.boogie_path = args.boogie
    config.z3_path = args.z3
    config.mypy_path = args.mypy_path

    os.environ['MYPYPATH'] = config.mypy_path
    jvm = JVM(config.classpath)
    try:
        prog = translate(python_file, jvm)
        if args.verbose:
            print('Translation successful.')
        if args.print_silver:
            if args.verbose:
                print('Result:')
            print(prog)
        vresult = verify(prog, python_file, jvm)
        if args.verbose:
            print("Verification completed.")
        print(vresult)
        if vresult:
            sys.exit(0)
        else:
            sys.exit(1)
    except (TypeException, InvalidProgramException) as e:
        print("Translation failed")
        if isinstance(e, InvalidProgramException):
            print('Line ' + str(e.node.lineno) + ': ' + e.code)
            if e.message:
                print(e.message)
        sys.exit(1)


if __name__ == '__main__':
    main()

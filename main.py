import ast
import astpp
import os
import sys

from analyzer import Analyzer
from jpype import JavaException
from jvmaccess import JVM
from os.path import expanduser
from translator import Translator, InvalidProgramException
from typeinfo import TypeInfo, TypeException
from verifier import Carbon, Silicon, VerificationResult, ViperVerifier
from viper_ast import ViperAST


def get_mypy_dir() -> str:
    (first, second, _, _, _) = sys.version_info
    userdir = expanduser('~')
    possible_dirs = [userdir + '/.local/bin',
                     'usr/local/bin'] if os.name == 'posix' else [
        'C:\Python' + str(first) + str(second) + '\Scripts']
    for dir in possible_dirs:
        if os.path.isdir(dir):
            if 'mypy' in os.listdir(dir):
                return os.path.join(dir, 'mypy')
    return None


def translate(path: str, jvm: JVM, mypydir: str):
    """
    Translates the Python module at the given path to a Viper program
    """
    types = TypeInfo()
    typecorrect = types.check(path, mypydir)
    try:
        if typecorrect:
            with open(path, 'r') as file:
                text = file.read()
            parseresult = ast.parse(text)
            print(astpp.dump(parseresult))
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


def main_translate() -> None:
    if len(sys.argv) < 3:
        print("Usage: py2viper py_file_path viper_jar_path [mypy_path]")
        exit(1)
    path = sys.argv[1]
    viperjar = sys.argv[2]
    try:
        mypydir = sys.argv[3]
    except IndexError:
        mypydir = get_mypy_dir()
        if mypydir is None:
            print(
                "Could not find mypy. Please provide path to mypy as third argument.")
            exit()
    jvm = JVM(viperjar)
    try:
        prog = translate(path, jvm, mypydir)
        print("Translation successful. Result:")
        print(prog)
        vresult = verify(prog, path, jvm)
        print("Verification completed.")
        print(vresult)
    except (TypeException, InvalidProgramException) as e:
        print("Translation failed")
        if isinstance(e, InvalidProgramException):
            print('Line ' + str(e.node.lineno) + ': ' + e.code)
            if e.message:
                print(e.message)


if __name__ == '__main__':
    main_translate()

import ast
import sys

from jpype import JavaException

from typeinfo import TypeInfo
from translator import Translator
from verifier import Verifier,VerificationResult
from jvmaccess import JVM
import os
from os.path import expanduser, isdir

def get_mypy_dir() -> str:
    (first, second, _, _, _) = sys.version_info
    userdir = expanduser('~')
    possible_dirs = [userdir + '/.local/bin', 'usr/local/bin'] if os.name == 'posix' else ['C:\Python' + str(first) + str(second) + '\Scripts']
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
    typecorrect = types.init(path, mypydir)
    try:
        if typecorrect:
            file = open(path, 'r')
            text = file.read()
            file.close()
            parseresult = ast.parse(text)
            # print(astpp.dump(parseresult))
            translator = Translator(jvm, path, types)
            prog = translator.translate_module(parseresult)
            return prog
        else:
            return None
    except JavaException as je:
        print(je.stacktrace())


def verify(prog: 'viper.silver.ast.Program', path: str, jvm: JVM) -> VerificationResult:
    """
    Verifies the given Viper program
    """
    try:
        verifier = Verifier(jvm, path)
        vresult = verifier.verify(prog)
        return vresult
    except JavaException as je:
        print(je.stacktrace())


def main_translate() -> None:
    try:
        path = sys.argv[1]
    except IndexError:
        print("Please provide name of file to verify.")
        exit()
    try:
        viperjar = sys.argv[2]
    except IndexError:
        print("Please provide path to viper jar as second argument")
        exit()
    try:
        mypydir = sys.argv[3]
    except IndexError:
        mypydir = get_mypy_dir()
        if mypydir is None:
            print("Could not find mypy. Please provide path to mypy as third argument.")
            exit()
    jvm = JVM(viperjar)
    prog = translate(path, jvm, mypydir)
    if prog is None:
        print("Translation failed")
    else:
        print("Translation successful. Result:")
        print(prog)
        vresult = verify(prog, path, jvm)
        print("Verification completed.")
        print(vresult)


if __name__ == '__main__':
    main_translate()

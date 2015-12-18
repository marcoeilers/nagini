import ast
import sys

from jpype import JavaException

from typeinfo import TypeInfo
from translator import Translator
from verifier import Verifier
from jvmaccess import JVM


def translate(path: str, jvm: JVM, mypydir: str):
    """
    Translates the Python module at the given path to a Viper program
    :param path:
    :param jvm:
    :param mypydir:
    :return:
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


def verify(prog, path, jvm):
    """
    Verifies the given Viper program
    :param prog:
    :param path:
    :param jvm:
    :return:
    """
    try:
        verifier = Verifier(jvm, path)
        vresult = verifier.verify(prog)
        return vresult
    except JavaException as je:
        print(je.stacktrace())


def main_translate() -> None:
    path = sys.argv[1]
    viperjar = sys.argv[2]
    try:
        mypydir = sys.argv[3]
    except IndexError:
        mypydir = '/home/marco/.local/bin/mypy'
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

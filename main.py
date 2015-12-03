from typeinfo import TypeInfo
from translator import Translator
from verifier import Verifier
from jvmaccess import JVM
from jpype import JavaException
import testing
import ast
import astpp
import sys


def translate(path, jvm, mypydir):
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


def compare_translation(sil_path, py_path, jvm, mypydir):
    prog = translate(py_path, jvm, mypydir)
    parser = getattr(getattr(jvm.viper.silver.parser, "Parser$"), "MODULE$")
    file = open(sil_path, 'r')
    text = file.read()
    file.close()
    parsed = parser.parse(text, None)
    if isinstance(parsed, getattr(jvm.scala.util.parsing.combinator,
                                  'Parsers$Success')):
        resolver = jvm.viper.silver.parser.Resolver(parsed.result())
        resolved = resolver.run()
        resolved = resolved.get()
        translator = jvm.viper.silver.parser.Translator(resolved)
        # consistency = getattr(getattr(jvm.viper.silver.ast.utility, 'Consistency$'), 'MODULE$')
        program = translator.translate()
        print(prog)
        print(program.get())
        if program.get().equals(prog):
            print("Translation correct")
        else:
            print("Translation incorrect")


def main_translate() -> None:
    path = sys.argv[1]
    try:
        viperjar = sys.argv[2]
    except IndexError:
        viperjar = '/viper/git/silicon_qp/target/scala-2.11/silicon-quantified-permissions.jar'
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
        # print(vresult)
        testing.evaluate_result(vresult, path, jvm)


def main_compare_translated():
    path = sys.argv[1]
    try:
        viperjar = sys.argv[2]
    except IndexError:
        viperjar = '/viper/git/silicon_qp/target/scala-2.11/silicon-quantified-permissions.jar'
    try:
        mypydir = sys.argv[3]
    except IndexError:
        mypydir = '/home/marco/.local/bin/mypy'
    jvm = JVM(viperjar)
    if not path.endswith('.py'):
        raise Exception()
    sil_path = path[:len(path) - 3] + '.sil'
    compare_translation(sil_path, path, jvm, mypydir)


if __name__ == '__main__':
    main_translate()

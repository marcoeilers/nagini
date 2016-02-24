import ast
import astpp
import os
import re
import sys

from analyzer import Analyzer
from jpype import JavaException
from jvmaccess import JVM
from os.path import expanduser
from translator import Translator, InvalidProgramException
from typeinfo import TypeInfo, TypeException
from verifier import Carbon, Silicon, VerificationResult, ViperVerifier, Failure
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


def parse_sil_file(sil_path: str, jvm):
    parser = getattr(getattr(jvm.viper.silver.parser, "Parser$"), "MODULE$")
    file = open(sil_path, 'r')
    text = file.read()
    file.close()
    parsed = parser.parse(text, None)
    assert (isinstance(parsed, getattr(jvm.scala.util.parsing.combinator,
                              'Parsers$Success')))
    resolver = jvm.viper.silver.parser.Resolver(parsed.result())
    resolved = resolver.run()
    resolved = resolved.get()
    translator = jvm.viper.silver.parser.Translator(resolved)
    program = translator.translate()
    return program.get()


def translate(path: str, jvm: JVM, mypydir: str):
    """
    Translates the Python module at the given path to a Viper program
    """
    try:
        builtins = ['/home/marco/scion/git/py2viper/contracts/bltns.py']
        native_sil =  ['/home/marco/scion/git/py2viper/translation/testinput.sil']
        list = "{'list': {'methods': {'__init__': {'args': [],'type': None},'append': {'args': ['List', 'int'],'type': None},'get': {'args': ['List', 'int'],'type': 'int'}}}}"
        sil_interface = [list]
        sil_programs = [parse_sil_file(sil_path, jvm) for sil_path in native_sil]
        modules = [path] + builtins
        viperast = ViperAST(jvm, jvm.java, jvm.scala, jvm.viper, path)
        types = TypeInfo()
        analyzer = Analyzer(jvm, viperast, types)
        for si in sil_interface:
            analyzer.add_interface(ast.literal_eval(si))
        for module in modules:
            typecorrect = types.check(module, mypydir)
            if typecorrect:
                with open(module, 'r') as file:
                    text = file.read()
                parseresult = ast.parse(text)
                # print(astpp.dump(parseresult))
                analyzer.set_contract_only(module != path)
                analyzer.visit_default(parseresult)
            else:
                return None
        translator = Translator(jvm, path, types, viperast)
        analyzer.process(translator)
        prog = translator.translate_program(analyzer.program, sil_programs)
        return prog
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

def to_list(seq):
    result = []
    iterator = seq.toIterator()
    while iterator.hasNext():
        result.append(iterator.next())
    return result


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
        # print("Translation successful. Result:")
        # print(prog)
        vresult = verify(prog, path, jvm)
        # print("Verification completed.")
        with open("/home/marco/.config/sublime-text-3/Packages/User/Py2Viper/tmp/errors.log", "w+") as f:
            if isinstance(vresult, Failure):
                for error in vresult.errors:
                    msgmatcher = re.compile("^(.*)\\(.*,\\d+:\\d+\\)$")
                    msg = msgmatcher.match(error.readableMessage()).groups()[0]
                    out = '(' + error.pos().toString() + ') ' + msg
                    print(out)
                    f.write(out + '\n')
            else:
                print(vresult)
    except (TypeException, InvalidProgramException) as e:
        print("Translation failed")
        if isinstance(e, InvalidProgramException):
            print('Line ' + str(e.node.lineno) + ': ' + e.code)
            if e.message:
                print(e.message)


if __name__ == '__main__':
    main_translate()

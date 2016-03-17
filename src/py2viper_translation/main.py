import argparse
import ast
import inspect
import os
import sys
import traceback

from jpype import JavaException
from py2viper_translation import config
from py2viper_translation.analyzer import Analyzer
from py2viper_translation.jvmaccess import JVM
from py2viper_translation.translator import Translator, InvalidProgramException
from py2viper_translation.typeinfo import TypeInfo, TypeException
from py2viper_translation.verifier import (
    Carbon,
    Silicon,
    VerificationResult,
    ViperVerifier,
    Failure)
from py2viper_translation.viper_ast import ViperAST

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


def translate(path: str, jvm: JVM):
    """
    Translates the Python module at the given path to a Viper program
    """
    current_path = os.path.dirname(inspect.stack()[0][1])
    resources_path = current_path + os.sep + 'resources' + os.sep
    builtins = []
    native_sil = [resources_path + 'preamble.sil']
    with open(resources_path + 'preamble.index', 'r') as file:
        sil_interface = [file.read()]
    sil_programs = [parse_sil_file(sil_path, jvm) for sil_path in native_sil]
    modules = [path] + builtins
    viperast = ViperAST(jvm, jvm.java, jvm.scala, jvm.viper, path)
    types = TypeInfo()
    analyzer = Analyzer(jvm, viperast, types, path)
    for si in sil_interface:
        analyzer.add_interface(ast.literal_eval(si))
    for module in analyzer.modules:
        analyzer.collect_imports(module)
        typecorrect = types.check(module)
        if typecorrect:
            analyzer.set_contract_only(module != os.path.abspath(path))
            analyzer.visit_module(module)
        else:
            return None
    translator = Translator(jvm, path, types, viperast)
    analyzer.process(translator)
    prog = translator.translate_program(analyzer.program, sil_programs)
    return prog


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
        traceback.print_exc()

def to_list(seq):
    result = []
    iterator = seq.toIterator()
    while iterator.hasNext():
        result.append(iterator.next())
    return result


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
    parser.add_argument(
        '--verifier',
        help='verifier to be used (carbon or silicon)',
        default='silicon'
    )
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
        if args.verifier == 'silicon':
            backend = ViperVerifier.silicon
        elif args.verifier == 'carbon':
            backend = ViperVerifier.carbon
        else:
            raise ValueError('Unknown verifier specified: ' + args.backend)
        vresult = verify(prog, python_file, jvm, backend=backend)
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
            raise e
        sys.exit(1)
    except JavaException as e:
        print(e.stacktrace())
        raise e


if __name__ == '__main__':
    main()

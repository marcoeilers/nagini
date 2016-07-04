import argparse
import astunparse
import inspect
import json
import logging
import os
import sys
import traceback

from jpype import JavaException
from py2viper_translation.analyzer import Analyzer
from py2viper_translation.lib import config
from py2viper_translation.lib.errors import cache
from py2viper_translation.lib.jvmaccess import JVM
from py2viper_translation.lib.program_nodes import ProgramNodeFactory
from py2viper_translation.lib.typeinfo import TypeException, TypeInfo
from py2viper_translation.lib.util import InvalidProgramException
from py2viper_translation.lib.viper_ast import ViperAST
from py2viper_translation.sif.lib.program_nodes import SIFProgramNodeFactory
from py2viper_translation.sif_translator import SIFTranslator
from py2viper_translation.translator import Translator
from py2viper_translation.verifier import (
    Carbon,
    Silicon,
    VerificationResult,
    ViperVerifier
)


def parse_sil_file(sil_path: str, jvm):
    parser = getattr(getattr(jvm.viper.silver.parser, "Parser$"), "MODULE$")
    file = open(sil_path, 'r')
    text = file.read()
    file.close()
    parsed = parser.parse(text, None)
    assert (isinstance(parsed, getattr(jvm.scala.util.parsing.combinator,
                                       'Parsers$Success')))
    parse_result = parsed.result()
    parse_result.initTreeProperties()
    resolver = jvm.viper.silver.parser.Resolver(parse_result)
    resolved = resolver.run()
    resolved = resolved.get()
    translator = jvm.viper.silver.parser.Translator(resolved)
    program = translator.translate()
    return program.get()


def translate(path: str, jvm: JVM, sif: bool = False):
    """
    Translates the Python module at the given path to a Viper program
    """
    cache.clear()
    current_path = os.path.dirname(inspect.stack()[0][1])
    resources_path = os.path.join(current_path, 'resources')
    builtins = []
    sil_files = ['bool.sil', 'set_dict.sil', 'list.sil', 'str.sil', 'tuple.sil',
                 'func_triple.sil']
    native_sil = [os.path.join(resources_path, f) for f in sil_files]
    with open(os.path.join(resources_path, 'preamble.index'), 'r') as file:
        sil_interface = [file.read()]
    sil_programs = [parse_sil_file(sil_path, jvm) for sil_path in native_sil]
    modules = [path] + builtins
    viperast = ViperAST(jvm, jvm.java, jvm.scala, jvm.viper, path)
    types = TypeInfo()
    if sif:
        node_factory = SIFProgramNodeFactory()
    else:
        node_factory = ProgramNodeFactory()
    analyzer = Analyzer(jvm, viperast, types, path, node_factory)
    for si in sil_interface:
        analyzer.add_interface(json.loads(si))
    for module in analyzer.modules:
        analyzer.collect_imports(module)
        type_correct = types.check(module)
        if type_correct:
            analyzer.contract_only = module != os.path.abspath(path)
            analyzer.visit_module(module)
        else:
            return None
    if sif:
        translator = SIFTranslator(jvm, path, types, viperast)
    else:
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
        print(prog)
        vresult = verifier.verify(prog)
        return vresult
    except JavaException as je:
        print(je.stacktrace())
        traceback.print_exc()


def _parse_log_level(log_level_string: str) -> int:
    """ Parses the log level provided by the user.
    """
    LOG_LEVELS = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']

    log_level_string_upper = log_level_string.upper()
    if log_level_string_upper in LOG_LEVELS:
        return getattr(logging, log_level_string_upper, logging.WARNING)
    else:
        msg = 'Invalid logging level {0} (expected one of: {1})'.format(
            log_level_string,
            LOG_LEVELS)
        raise argparse.ArgumentTypeError(msg)


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
        default='silicon')
    parser.add_argument(
        '--sif',
        action='store_true',
        help='Verify secure information flow')
    parser.add_argument(
        '--log',
        type=_parse_log_level,
        help='log level',
        default='WARNING')
    args = parser.parse_args()

    python_file = args.python_file
    config.classpath = args.viper_jar_path
    config.boogie_path = args.boogie
    config.z3_path = args.z3
    config.mypy_path = args.mypy_path
    logging.basicConfig(level=args.log)

    os.environ['MYPYPATH'] = config.mypy_path
    jvm = JVM(config.classpath)
    try:
        prog = translate(python_file, jvm, args.sif)
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
            print(astunparse.unparse(e.node))
        if isinstance(e, TypeException):
            for msg in e.messages:
                print(msg)
        sys.exit(1)
    except JavaException as e:
        print(e.stacktrace())
        raise e


if __name__ == '__main__':
    main()

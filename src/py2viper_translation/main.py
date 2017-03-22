import argparse
import astunparse
import inspect
import json
import logging
import os
import sys
import time
import traceback

# This import monkey-patches mypy and should happen as early as possible.
import py2viper_translation.mypy.mypy_patch

from jpype import JavaException
from py2viper_translation.analyzer import Analyzer
from py2viper_translation.lib import config
from py2viper_translation.lib.errors import error_manager
from py2viper_translation.lib.jvmaccess import JVM
from py2viper_translation.lib.typeinfo import TypeException, TypeInfo
from py2viper_translation.lib.util import InvalidProgramException
from py2viper_translation.lib.viper_ast import ViperAST
from py2viper_translation.sif_analyzer import SIFAnalyzer
from py2viper_translation.sif_translator import SIFTranslator
from py2viper_translation.translator import Translator
from py2viper_translation.verifier import (
    Carbon,
    Silicon,
    VerificationResult,
    ViperVerifier
)


def parse_sil_file(sil_path: str, jvm):
    parser = getattr(getattr(jvm.viper.silver.parser, "FastParser$"), "MODULE$")
    assert parser
    with open(sil_path, 'r') as file:
        text = file.read()
    path = jvm.java.nio.file.Paths.get(sil_path, [])
    parsed = parser.parse(text, path)
    assert (isinstance(parsed, getattr(jvm.fastparse.core,
                                       'Parsed$Success')))
    parse_result = parsed.value()
    parse_result.initProperties()
    resolver = jvm.viper.silver.parser.Resolver(parse_result)
    resolved = resolver.run()
    resolved = resolved.get()
    translator = jvm.viper.silver.parser.Translator(resolved)
    # Reset messages in global Consistency object. Otherwise, left-over
    # translation errors from previous translations prevent loading of the
    # built-in silver files.
    jvm.viper.silver.ast.utility.Consistency.resetMessages()
    program = translator.translate()
    return program.get()


sil_programs = []


def load_sil_files(jvm: JVM, sif: bool = False):
    current_path = os.path.dirname(inspect.stack()[0][1])
    resources_path = os.path.join(current_path, 'resources')
    if sif:
        resources_path = os.path.join(current_path, 'sif/resources')
    sil_programs.append(parse_sil_file(
        os.path.join(resources_path, 'all.sil'), jvm))


def translate(path: str, jvm: JVM, sif: bool = False,
              reload_resources: bool = False):
    """
    Translates the Python module at the given path to a Viper program
    """
    error_manager.clear()
    current_path = os.path.dirname(inspect.stack()[0][1])
    resources_path = os.path.join(current_path, 'resources')
    builtins = []
    with open(os.path.join(resources_path, 'preamble.index'), 'r') as file:
        sil_interface = [file.read()]

    modules = [path] + builtins
    viperast = ViperAST(jvm, jvm.java, jvm.scala, jvm.viper, path)
    types = TypeInfo()
    type_correct = types.check(os.path.abspath(path))
    if not type_correct:
        return None
    if sif:
        analyzer = SIFAnalyzer(jvm, viperast, types, path)
    else:
        analyzer = Analyzer(jvm, viperast, types, path)
    main_module = analyzer.module
    for si in sil_interface:
        analyzer.add_native_silver_builtins(json.loads(si))

    collect_modules(analyzer, path)
    if sif:
        translator = SIFTranslator(jvm, path, types, viperast)
    else:
        translator = Translator(jvm, path, types, viperast)
    analyzer.process(translator)
    global sil_programs
    if not sil_programs or reload_resources:
        sil_programs = []
        load_sil_files(jvm, sif)
    modules = [main_module.global_module] + list(analyzer.modules.values())
    prog = translator.translate_program(modules, sil_programs)
    return prog


def collect_modules(analyzer: Analyzer, path: str) -> None:
    """
    Starting from the main module, finds all imports and sets up all modules
    for them.
    """
    main_module = analyzer.module
    analyzer.module_index = 0
    analyzer.collect_imports(path)

    for module in analyzer.module_paths:
        if module.startswith('mod$'):
            continue
        if module != os.path.abspath(path):
            analyzer.contract_only = True
            analyzer.module = analyzer.modules[module]
            analyzer.visit_module(module)
        else:
            analyzer.module = main_module
            analyzer.contract_only = False
            analyzer.visit_module(module)


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
        '--write-silver-to-file',
        default=None,
        help='write generated Silver program to specified file')
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
    parser.add_argument(
        '--benchmark',
        type=int,
        help=('run verification the given number of times to benchmark '
              'performance'),
        default=-1)
    parser.add_argument(
        '--ide-mode',
        action='store_true',
        help='Output errors in IDE format')
    args = parser.parse_args()

    config.classpath = args.viper_jar_path
    config.boogie_path = args.boogie
    config.z3_path = args.z3
    config.mypy_path = args.mypy_path
    logging.basicConfig(level=args.log)

    os.environ['MYPYPATH'] = config.mypy_path
    jvm = JVM(config.classpath)
    translate_and_verify(args.python_file, jvm, args)


def translate_and_verify(python_file, jvm, args):
    try:
        prog = translate(python_file, jvm, args.sif)
        if args.verbose:
            print('Translation successful.')
        if args.print_silver:
            if args.verbose:
                print('Result:')
            print(str(prog))
        if args.write_silver_to_file:
            with open(args.write_silver_to_file, 'w') as fp:
                fp.write(str(prog))
        if args.verifier == 'silicon':
            backend = ViperVerifier.silicon
        elif args.verifier == 'carbon':
            backend = ViperVerifier.carbon
        else:
            raise ValueError('Unknown verifier specified: ' + args.verifier)
        if args.benchmark >= 1:
            for i in range(args.benchmark):
                start = time.time()
                vresult = verify(prog, python_file, jvm, backend=backend)
                end = time.time()
                assert vresult
                print("RUN,{},{},{},{},{}".format(
                    i, args.benchmark, start, end, end - start))
        else:
            vresult = verify(prog, python_file, jvm, backend=backend)
        if args.verbose:
            print("Verification completed.")
        print(vresult.to_string(args.ide_mode))
        if vresult:
            sys.exit(0)
        else:
            sys.exit(1)
    except (TypeException, InvalidProgramException) as e:
        print("Translation failed")
        if isinstance(e, InvalidProgramException):
            print(python_file + ':' + str(e.node.lineno) + ': error: ' + e.code)
            if e.message:
                print(e.message)
            print(astunparse.unparse(e.node))
        if isinstance(e, TypeException):
            for msg in e.messages:
                print(msg)
        sys.exit(2)
    except JavaException as e:
        print(e.stacktrace())
        raise e


if __name__ == '__main__':
    main()

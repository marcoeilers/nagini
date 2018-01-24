"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import argparse
import inspect
import json
import logging
import os
import re
import time
import traceback

# These imports monkey-patch mypy and should happen as early as possible.
import nagini_translation.mypy_patches.column_info_patch
import nagini_translation.mypy_patches.optional_patch

from jpype import JavaException
from nagini_translation.analyzer import Analyzer
from nagini_translation.lib import config
from nagini_translation.lib.constants import DEFAULT_SERVER_SOCKET
from nagini_translation.lib.errors import error_manager
from nagini_translation.lib.jvmaccess import JVM
from nagini_translation.lib.typeinfo import TypeException, TypeInfo
from nagini_translation.lib.util import InvalidProgramException, UnsupportedException
from nagini_translation.lib.viper_ast import ViperAST
from nagini_translation.sif_analyzer import SIFAnalyzer
from nagini_translation.sif_translator import SIFTranslator
from nagini_translation.translator import Translator
from nagini_translation.verifier import (
    Carbon,
    Silicon,
    VerificationResult,
    ViperVerifier
)
from typing import Set


TYPE_ERROR_PATTERN = r"^(?P<file>.*):(?P<line>\d+): error: (?P<msg>.*)$"
TYPE_ERROR_MATCHER = re.compile(TYPE_ERROR_PATTERN)


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
    translator = jvm.viper.silver.parser.Translator(resolved, False)
    # Reset messages in global Consistency object. Otherwise, left-over
    # translation errors from previous translations prevent loading of the
    # built-in silver files.
    jvm.viper.silver.ast.utility.Consistency.resetMessages()
    program = translator.translate()
    return program.get()


def load_sil_files(jvm: JVM, sif: bool = False):
    current_path = os.path.dirname(inspect.stack()[0][1])
    resources_path = os.path.join(current_path, 'resources')
    if sif:
        resources_path = os.path.join(current_path, 'sif/resources')
    return parse_sil_file(os.path.join(resources_path, 'all.sil'), jvm)


def translate(path: str, jvm: JVM, selected: Set[str] = set(),
              sif: bool = False, reload_resources: bool = False):
    """
    Translates the Python module at the given path to a Viper program
    """
    path = os.path.abspath(path)
    error_manager.clear()
    current_path = os.path.dirname(inspect.stack()[0][1])
    resources_path = os.path.join(current_path, 'resources')

    viperast = ViperAST(jvm, jvm.java, jvm.scala, jvm.viper, path)
    types = TypeInfo()
    type_correct = types.check(path)
    if not type_correct:
        return None

    if sif:
        analyzer = SIFAnalyzer(types, path, selected)
    else:
        analyzer = Analyzer(types, path, selected)
    main_module = analyzer.module
    with open(os.path.join(resources_path, 'preamble.index'), 'r') as file:
        analyzer.add_native_silver_builtins(json.loads(file.read()))

    main_module.add_builtin_vars()
    collect_modules(analyzer, path)
    if sif:
        translator = SIFTranslator(jvm, path, types, viperast)
    else:
        translator = Translator(jvm, path, types, viperast)
    analyzer.process(translator)
    if 'sil_programs' not in globals() or reload_resources:
        global sil_programs
        sil_programs = load_sil_files(jvm, sif)
    modules = [main_module.global_module] + list(analyzer.modules.values())
    prog = translator.translate_program(modules, sil_programs, selected)
    return prog


def collect_modules(analyzer: Analyzer, path: str) -> None:
    """
    Starting from the main module, finds all imports and sets up all modules
    for them.
    """
    analyzer.module_index = 0
    analyzer.collect_imports(path)

    analyzer.analyze()

    # Carry out all tasks that were deferred to the end of the analysis.
    for task in analyzer.deferred_tasks:
        task()


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
    parser.add_argument(
        '--select',
        default=None,
        help='select specific methods or classes to verify, separated by commas'
    )
    parser.add_argument(
        '--server',
        action='store_true',
        help='Start Nagini server'
    )
    args = parser.parse_args()

    config.classpath = args.viper_jar_path
    config.boogie_path = args.boogie
    config.z3_path = args.z3
    config.mypy_path = args.mypy_path

    if not config.classpath:
        parser.error('missing argument: --viper-jar-path')
    if not config.z3_path:
        parser.error('missing argument: --z3')
    if args.verifier == 'carbon' and not config.classpath:
        parser.error('missing argument: --boogie')

    logging.basicConfig(level=args.log)

    os.environ['MYPYPATH'] = config.mypy_path
    jvm = JVM(config.classpath)
    if args.server:
        import zmq
        context = zmq.Context()
        socket = context.socket(zmq.REP)
        socket.bind(DEFAULT_SERVER_SOCKET)
        global sil_programs
        sil_programs = load_sil_files(jvm, args.sif)

        while True:
            file = socket.recv_string()
            response = ['']

            def add_response(part):
                response[0] = response[0] + '\n' + part

            translate_and_verify(file, jvm, args, add_response)
            socket.send_string(response[0])
    else:
        translate_and_verify(args.python_file, jvm, args)


def translate_and_verify(python_file, jvm, args, print=print):
    try:
        selected = set(args.select.split(',')) if args.select else set()
        prog = translate(python_file, jvm, selected, args.sif)
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
    except (TypeException, InvalidProgramException, UnsupportedException) as e:
        print("Translation failed")
        if isinstance(e, (InvalidProgramException, UnsupportedException)):
            if isinstance(e, InvalidProgramException):
                issue = 'Invalid program: '
                if e.message:
                    issue += e.message
                else:
                    issue += e.code
            else:
                issue = 'Not supported: '
                if e.args[0]:
                    issue += e.args[0]
                else:
                    issue += str(e.node)
            line = str(e.node.lineno)
            col = str(e.node.col_offset)
            print(issue + ' (' + python_file + '@' + line + '.' + col + ')')
        if isinstance(e, TypeException):
            for msg in e.messages:
                parts = TYPE_ERROR_MATCHER.match(msg)
                if parts:
                    parts = parts.groupdict()
                    file = parts['file']
                    if file == '__main__':
                        file = python_file
                    msg = parts['msg']
                    line = parts['line']
                    print('Type error: ' + msg + ' (' + file + '@' + line + '.0)')
                else:
                    print(msg)
    except JavaException as e:
        print(e.stacktrace())
        raise e


if __name__ == '__main__':
    main()

"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import argparse
import astunparse
import inspect
import json
import logging
import os
import sys
import re
import time
import traceback


from jpype._jexception import JException
from nagini_translation.analyzer import Analyzer
from nagini_translation.sif_translator import SIFTranslator
from nagini_translation.lib import config
from nagini_translation.lib.constants import DEFAULT_SERVER_SOCKET
from nagini_translation.lib.errors import error_manager
from nagini_translation.lib.jvmaccess import (
    getclass,
    getobject,
    JVM
)
from nagini_translation.lib.typedefs import Program
from nagini_translation.lib.typeinfo import TypeException, TypeInfo
from nagini_translation.lib.util import (
    ConsistencyException,
    InvalidProgramException,
    UnsupportedException,
)
from nagini_translation.lib.viper_ast import ViperAST
from nagini_translation.sif.lib.util import (
    configure_mpp_transformation,
    set_all_low_methods,
    set_preserves_low_methods
)
from nagini_translation.sif.lib.viper_ast_extended import ViperASTExtended
from nagini_translation.translator import Translator
from nagini_translation.verifier import (
    Carbon,
    get_arp_plugin,
    Silicon,
    VerificationResult,
    ViperVerifier
)
from nagini_translation import verifier
from typing import List, Set, Tuple


TYPE_ERROR_PATTERN = r"^(?P<file>.*):(?P<line>\d+): error: (?P<msg>.*)$"
TYPE_ERROR_MATCHER = re.compile(TYPE_ERROR_PATTERN)


def parse_sil_file(sil_path: str, bv_path: str, bv_size: int, jvm, float_option: str = None):
    parser = getclass(jvm.java, jvm.viper.silver.parser, "FastParser")()
    tp = jvm.viper.silver.plugin.standard.termination.TerminationPlugin(None, None, None, parser)
    assert parser
    with open(sil_path, 'r') as file:
        text = file.read()
    with open(bv_path, 'r') as file:
        int_min = -(2 ** (bv_size - 1))
        int_max = 2 ** (bv_size - 1) - 1
        text += "\n" + file.read().replace("NBITS", str(bv_size)).replace("INT_MIN_VAL", str(int_min)).replace("INT_MAX_VAL", str(int_max))
    if float_option == "real":
        text = text.replace("float.sil", "float_real.sil")
    if float_option == "ieee32":
        text = text.replace("float.sil", "float_ieee32.sil")
    path = jvm.java.nio.file.Paths.get(sil_path, [])
    none = getobject(jvm.java, jvm.scala, "None")
    tp.beforeParse(text, False)
    diskloader = getobject(jvm.java, jvm.viper.silver.ast.utility, "DiskLoader")
    parsed = parser.parse(text, path, none, diskloader)

    parse_result = parsed
    parse_result.initProperties()
    resolver = jvm.viper.silver.parser.Resolver(parse_result)
    resolved = resolver.run()
    resolved = resolved.get()
    translator = getobject(jvm.java, jvm.viper.silver.parser, 'Translator').apply(resolved)
    # Reset messages in global Consistency object. Otherwise, left-over
    # translation errors from previous translations prevent loading of the
    # built-in silver files.
    jvm.viper.silver.ast.utility.Consistency.resetMessages()
    program = translator.translate()
    return program.get()


def load_sil_files(jvm: JVM, bv_size: int, sif: bool = False, float_option: str = None):
    current_path = os.path.dirname(inspect.stack()[0][1])
    default_path = os.path.join(current_path, 'resources')
    if sif:
        resources_path = os.path.join(current_path, 'sif', 'resources')
    else:
        resources_path = default_path
    return parse_sil_file(os.path.join(resources_path, 'all.sil'), os.path.join(default_path, 'intbv.sil'), bv_size, jvm, float_option)


def translate(path: str, jvm: JVM, bv_size: int, selected: Set[str] = set(), base_dir: str = None,
              sif: bool = False, arp: bool = False, ignore_global: bool = False,
              reload_resources: bool = False, verbose: bool = False,
              check_consistency: bool = False, float_encoding: str = None,
              counterexample: bool = False) -> Tuple[List['PythonModule'], Program]:
    """
    Translates the Python module at the given path to a Viper program
    """
    path = os.path.abspath(path)
    error_manager.clear()
    current_path = os.path.dirname(inspect.stack()[0][1])
    if sif:
        builtins_index_path = os.path.join(current_path, 'sif', 'resources')
    else:
        builtins_index_path = os.path.join(current_path, 'resources')

    if sif:
        viper_ast = ViperASTExtended(jvm, jvm.java, jvm.scala, jvm.viper, path)
    else:
        viper_ast = ViperAST(jvm, jvm.java, jvm.scala, jvm.viper, path)
    if not viper_ast.is_available():
        raise Exception('Viper not found on classpath.')
    if sif and not viper_ast.is_extension_available():
        raise Exception('Viper AST SIF extension not found on classpath.')
    types = TypeInfo()
    type_correct = types.check(path, base_dir)
    if not type_correct:
        return None

    analyzer = Analyzer(types, path, selected)
    main_module = analyzer.module
    with open(os.path.join(builtins_index_path, 'builtins.json'), 'r') as file:
        analyzer.add_native_silver_builtins(json.loads(file.read()))

    analyzer.initialize_io_analyzer()
    main_module.add_builtin_vars()
    collect_modules(analyzer, path)
    if sif:
        translator = SIFTranslator(jvm, path, types, viper_ast)
    else:
        translator = Translator(jvm, path, types, viper_ast)
    analyzer.process(translator)
    if 'sil_programs' not in globals() or reload_resources:
        global sil_programs
        sil_programs = load_sil_files(jvm, bv_size, sif, float_encoding)
    modules = [main_module.global_module] + list(analyzer.modules.values())
    prog = translator.translate_program(modules, sil_programs, selected,
                                        arp=arp, ignore_global=ignore_global, sif=sif, float_encoding=float_encoding)
    if sif:
        set_all_low_methods(jvm, viper_ast.all_low_methods)
        set_preserves_low_methods(jvm, viper_ast.preserves_low_methods)
    if verbose:
        print('Translation successful.')
    if sif:
        configure_mpp_transformation(jvm,
                                     ctrl_opt=True,
                                     seq_opt=True,
                                     act_opt=True,
                                     func_opt=True,
                                     all_low=analyzer.has_all_low)
        if counterexample:
            prog = getobject(jvm.java, jvm.viper.silicon.sif, 'CounterexampleSIFTransformerO').transform(prog, False)
        else:
            prog = getobject(jvm.java, jvm.viper.silver.sif, 'SIFExtendedTransformer').transform(prog, False)
        if verbose:
            print('Transformation to MPP successful.')
    if arp:
        prog = get_arp_plugin(jvm).before_verify(prog)
        if verbose:
            print('ARP transformation successful.')
    if check_consistency:
        # Run consistency check in translated AST
        consistency_errors = viper_ast.to_list(prog.checkTransitively())
        for error in consistency_errors:
            print(error.toString())
        if consistency_errors:
            raise ConsistencyException('consistency.error')
    return modules, prog


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


def verify(modules, prog: 'viper.silver.ast.Program', path: str, jvm: JVM, viper_args: List[str],
           backend=ViperVerifier.silicon, arp=False, counterexample=False, sif=False) -> VerificationResult:
    """
    Verifies the given Viper program
    """
    try:
        if backend == ViperVerifier.silicon:
            verifier = Silicon(jvm, path, viper_args, counterexample)
        elif backend == ViperVerifier.carbon:
            verifier = Carbon(jvm, path, viper_args)
        vresult = verifier.verify(modules, prog, arp=arp, sif=sif)
        return vresult
    except JException as je:
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
        '--base-dir',
        help='base directory',
        default=None)
    parser.add_argument(
        '--print-viper',
        action='store_true',
        help='print generated Viper program')
    parser.add_argument(
        '--write-viper-to-file',
        default=None,
        help='write generated Viper program to specified file')
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
        nargs='?',
        const='true',
        default=False,
        help='verify secure information flow')
    parser.add_argument(
        '--show-viper-errors',
        action='store_true',
        help='show Viper-level error messages if no Python errors are available')
    parser.add_argument(
        '--arp',
        action='store_true',
        help='Use Abstract Read Permissions')
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
        '--ignore-global',
        action='store_true',
        help='do not verify the top level program (global statements)'
    )
    parser.add_argument(
        '--ignore-obligations',
        action='store_true',
        help='do not verify liveness properties (obligations)'
    )
    parser.add_argument(
        '--server',
        action='store_true',
        help='start Nagini server'
    )
    parser.add_argument(
        '--counterexample',
        action='store_true',
        help='return a counterexample for every verification error if possible'
    )
    parser.add_argument(
        '--viper-arg',
        help='Arguments to be forwarded to Viper, separated by commas'
    )
    parser.add_argument(
        '--float-encoding',
        help='float encoding to be used (real or ieee32)',
        default=None
    )
    parser.add_argument(
        '--submit-for-evaluation',
        help='Allow Nagini and Viper developers to store the current program for future evaluation.',
        action='store_true',
        default=False,
    )
    parser.add_argument(
        '--int-bitops-size',
        help='Maximium size of integers for which bitwise operations are allowed.',
        type=int,
        default=8
    )
    args = parser.parse_args()

    config.classpath = args.viper_jar_path
    config.boogie_path = args.boogie
    config.z3_path = args.z3
    config.mypy_path = args.mypy_path
    config.set_verifier(args.verifier)
    if args.ignore_obligations:
        config.obligation_config.disable_all = True

    if not config.classpath:
        parser.error('missing argument: --viper-jar-path')
    if not config.z3_path:
        parser.error('missing argument: --z3')
    if args.verifier and (args.verifier not in ('silicon', 'carbon')):
        parser.error('invalid value for --verifier option')
    if args.verifier == 'carbon' and not config.classpath:
        parser.error('missing argument: --boogie')
    if args.verifier != 'silicon' and args.counterexample:
        parser.error('counterexamples only supported with Silicon backend')
    if args.sif not in ('true', False, 'poss', 'prob'):
        parser.error('invalid value for --sif option')
    if args.float_encoding and (args.float_encoding not in ('real', 'ieee32')):
        parser.error('invalid value for --float-encoding option')

    logging.basicConfig(level=args.log)

    jvm = JVM(config.classpath)
    if args.server:
        import zmq
        context = zmq.Context()
        socket = context.socket(zmq.REP)
        socket.bind(DEFAULT_SERVER_SOCKET)
        global sil_programs
        sil_programs = load_sil_files(args.int_bitops_size, args.jvm, args.sif, args.float_encoding)

        while True:
            file = socket.recv_string()
            response = ['']

            def add_response(part):
                response[0] = response[0] + '\n' + part

            translate_and_verify(file, jvm, args, add_response, arp=args.arp, base_dir=args.base_dir)
            socket.send_string(response[0])
    else:
        success = translate_and_verify(args.python_file, jvm, args, arp=args.arp, base_dir=args.base_dir)
        sys.exit(0 if success else 1)


def translate_and_verify(python_file, jvm, args, print=print, arp=False, base_dir=None) -> bool:
    """
    Translates input file to viper code and dispatches result to backend for verification

    :returns: Whether translation and verification was successful
    """
    try:
        start = time.time()
        selected = set(args.select.split(',')) if args.select else set()
        modules, prog = translate(python_file, jvm, args.int_bitops_size, selected=selected, sif=args.sif, base_dir=base_dir,
                                  ignore_global=args.ignore_global, arp=arp, verbose=args.verbose,
                                  counterexample=args.counterexample, float_encoding=args.float_encoding)
        if args.print_viper:
            if args.verbose:
                print('Result:')
            print(str(prog))
        if args.write_viper_to_file:
            with open(args.write_viper_to_file, 'w') as fp:
                fp.write(str(prog))
        if args.verifier == 'silicon':
            backend = ViperVerifier.silicon
        elif args.verifier == 'carbon':
            backend = ViperVerifier.carbon
        else:
            raise ValueError('Unknown verifier specified: ' + args.verifier)
        viper_args = [] if args.viper_arg is None else args.viper_arg.split(",")
        if args.benchmark >= 1:
            print("Run, Total, Start, End, Time".format())
            for i in range(args.benchmark):
                start = time.time()
                modules, prog = translate(python_file, jvm, selected=selected, sif=args.sif, arp=arp, base_dir=base_dir,
                                          ignore_global=args.ignore_global, float_encoding=args.float_encoding)
                vresult = verify(modules, prog, python_file, jvm, viper_args, backend=backend, arp=arp)
                end = time.time()
                print("{}, {}, {}, {}, {}".format(
                    i, args.benchmark, start, end, end - start))
        else:
            submitter = None
            if args.submit_for_evaluation:
                submitter = jvm.viper.silver.utility.ManualProgramSubmitter(True, "", "Nagini", backend.name.capitalize(), viper_args)
                submitter.setProgram(prog)

            vresult = verify(modules, prog, python_file, jvm, viper_args,
                             backend=backend, arp=arp, counterexample=args.counterexample, sif=args.sif)
            
            if submitter is not None:
                submitter.setSuccess(vresult.__bool__())
                submitter.submit()
        if args.verbose:
            print("Verification completed.")
        print(vresult.to_string(args.ide_mode, args.show_viper_errors))
        duration = '{:.2f}'.format(time.time() - start)
        print('Verification took ' + duration + ' seconds.')
        return isinstance(vresult, verifier.Success)
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
                    issue += astunparse.unparse(e.node)
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
        return False
    except ConsistencyException as e:
        print(e.message + ': Translated AST contains inconsistencies.')
        return False

    except JException as e:
        print(e.stacktrace())
        raise e


if __name__ == '__main__':
    main()

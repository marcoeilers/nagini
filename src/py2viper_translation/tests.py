import io
import os
import pytest
import re
import tokenize

from os.path import isfile, join
from py2viper_translation.lib import config, jvmaccess
from py2viper_translation.lib.errors import cache
from py2viper_translation.lib.typeinfo import TypeException
from py2viper_translation.lib.util import InvalidProgramException, flatten, flatten_dict
from py2viper_translation.main import translate, verify
from py2viper_translation.verifier import VerificationResult, ViperVerifier
from typing import Any, Dict, List, Tuple

test_translation_dir = 'tests/translation/'
test_verification_dir = 'tests/verification/'
test_sif_dir = 'tests/sif/'

os.environ['MYPYPATH'] = config.mypy_path

verifiers = [ViperVerifier.silicon]
if config.boogie_path:
    verifiers.append(ViperVerifier.carbon)

assert config.classpath
jvm = jvmaccess.JVM(config.classpath)

type_error_pattern = "^(.*):(\\d+): error: (.*)$"
mypy_error_matcher = re.compile(type_error_pattern)


class AnnotatedTests():
    def _is_annotation(self, tk: tokenize.TokenInfo) -> bool:
        """
        A test annotation is a comment starting with #::
        """
        return (tk.type is tokenize.COMMENT and
                tk.string.strip().startswith('#:: ') and
                tk.string.strip().endswith(')'))

    def _is_ignore_annotation(self, tk: tokenize.TokenInfo) -> bool:
        return (tk.type is tokenize.COMMENT and
                tk.string.strip().startswith('#:: IgnoreFile'))

    def get_test_annotations(self, path: str) -> List:
        """
        Retrieves test annotations from the given Python source file
        """
        with open(path, 'r') as file:
            text = file.read()
        filebytes = io.BytesIO(bytes(text, 'utf-8'))
        tokens = tokenize.tokenize(filebytes.readline)
        test_annotations = [tk for tk in tokens if self._is_annotation(tk)]
        return test_annotations

    def extract_annotations(self, token) -> Dict[str, List[Any]]:
        matcher = re.compile('([a-zA-Z]+)\(([a-zA-z\.,_:;\d ?\'"]+)\)')
        result = {'ExpectedOutput': [],
                  'OptionalOutput': [],
                  'Label': []}
        content = token.string.strip()[3:].strip()
        stripped_list = [part.strip() for part in content.split('|')]
        for part in stripped_list:
            match = matcher.match(part)
            if match:
                type, content = match.group(1, 2)
                if type == 'ExpectedOutput':
                    result['ExpectedOutput'].append(
                        self.token_to_expected(content, token))
                elif type == 'OptionalOutput':
                    result['OptionalOutput'].append(
                        self.token_to_expected(content, token))
                elif type == 'Label':
                    result['Label'].append(
                        self.token_to_label(content, token))
                else:
                    raise ValueError(type)
            else:
                raise ValueError(part)
        return result

    def token_to_expected(self, content, token):
        if content.startswith('type.error:'):
            # Type errors need special treatment because they contain
            # error text, not ids.
            return (token.start, (content, ()))
        split = content.split(',')
        id = split[0]
        vias = split[1:]
        return (token.start, (id, vias))

    def token_to_label(self, content, token):
        return (content, token.start[0])

    def get_vias(self, error) -> str:
        reason_pos = error.reason().offendingNode().pos()
        if hasattr(reason_pos, 'id'):
            reason_pos = reason_pos.id()
            reason_entry = cache[reason_pos]
            if reason_entry[1]:
                return [via[1].line() for via in reason_entry[1]]
        error_pos = error.pos()
        if hasattr(error_pos, 'id'):
            error_pos = error_pos.id()
            error_entry = cache[error_pos]
            return [via[1].line() for via in error_entry[1]]
        return []

    def failure_to_actual(self, error: 'silver.verifier.AbstractError') \
            -> Tuple[int, int, str, str, List[int]]:
        return ((error.pos().line(), error.pos().column()), error.fullId(),
                error.readableMessage(), self.get_vias(error))

    def compare_actual_expected(self, actual, expected, optional, labels):
        actual_unexpected = []
        missing_expected = []
        expected = [(l, i, [labels[i] for i in v]) for (l, i, v) in expected]
        for ae in actual:
            (line, id, vias) = ae
            vias_decrement = [via - 1 for via in vias]
            key = (line - 1, id, vias_decrement)
            if not key in expected and not key in optional:
                actual_unexpected += [ae]
        for ee in expected:
            (line, id, vias) = ee
            vias_increment = [via + 1 for via in vias]
            if not (line + 1, id, vias_increment) in actual:
                missing_expected += [ee]
        assert not actual_unexpected
        assert not missing_expected


class VerificationTests(AnnotatedTests):
    def test_file(self, path: str, jvm, verifier, sif):
        test_annotations = self.get_test_annotations(path)
        if any(self._is_ignore_annotation(tk) for tk in test_annotations):
            pytest.skip()
        prog = translate(path, jvm, sif)
        assert prog is not None
        vresult = verify(prog, path, jvm, verifier)
        self.evaluate_result(vresult, path, test_annotations, jvm)

    def evaluate_result(self, vresult: VerificationResult, file_path: str,
                        test_annotations: List, jvm: jvmaccess.JVM):
        """
        Evaluates the verification result w.r.t. the test annotations in
        the file
        """

        annotations = flatten_dict([self.extract_annotations(ann) for ann
                                    in test_annotations
                                    if ann.string.strip().startswith('#::')],
                                   {'ExpectedOutput', 'OptionalOutput',
                                    'Label'})
        expected = annotations['ExpectedOutput']
        expected_lo = [(line, id, vias) for ((line, col), (id, vias)) in
                       expected]
        optional = annotations['OptionalOutput']
        optional_lo = [(line, id, vias) for ((line, col), (id, vias)) in
                       optional]
        labels = annotations['Label']
        labels_dict = {key: value for (key, value) in labels}
        if vresult:
            assert not expected
        else:
            # make sure we produce an error string
            print(vresult)
            missing_info = [error for error in vresult.errors if
                            not isinstance(error.pos(),
                                           jvm.viper.silver.ast.HasLineColumn)]
            actual = [self.failure_to_actual(error) for error in vresult.errors
                      if not error in missing_info]
            actual_lo = [(line, id, via) for ((line, col), id, msg, via) in
                         actual]
            assert not missing_info
            self.compare_actual_expected(actual_lo, expected_lo, optional_lo,
                                         labels_dict)


verification_tester = VerificationTests()


def _test_files(test_dir):
    result = []
    for root, dir_names, file_names in os.walk(
            test_dir,
            topdown=True):
        if 'tests' in file_names:
            # tests file lists all tests in this directory, so we read
            # its contents and do not proceed deeper.
            with open(join(root, 'tests')) as fp:
                for file_name in fp:
                    result.append(join(root, file_name.strip()))
            dir_names.clear()
            continue
        if 'resources' in dir_names:
            # Skip resources directory.
            dir_names.remove('resources')
        for file_name in file_names:
            if file_name.endswith('.py'):
                result.append(join(root, file_name))
    return sorted(result)


def verification_test_files():
    files = _test_files(test_verification_dir)
    result = []
    for file in files:
        result.extend([(file, verifier) for verifier in verifiers])
    return result


@pytest.mark.parametrize('path,verifier', verification_test_files())
def test_verification(path, verifier):
    verification_tester.test_file(path, jvm, verifier, False)


class TranslationTests(AnnotatedTests):
    def extract_mypy_error(self, message):
        parts = mypy_error_matcher.match(message).groups()
        offset = 3 if parts[0] is None else 0
        reason = parts[2 + offset].strip()
        if '(' in reason:
            reason = reason.split('(')[0].strip()
        return (int(parts[1 + offset]),
                'type.error:' + reason, [])

    def test_file(self, path: str, jvm):
        test_annotations = self.get_test_annotations(path)
        if any(self._is_ignore_annotation(tk) for tk in test_annotations):
            pytest.skip()
        annotations = flatten_dict([self.extract_annotations(ann) for ann
                                    in test_annotations
                                    if ann.string.strip().startswith('#::')],
                                   {'ExpectedOutput', 'OptionalOutput',
                                    'Label'})
        expected = annotations['ExpectedOutput']
        expected_lo = [(line, id, vias) for ((line, col), (id, vias)) in
                       expected]
        optional = annotations['OptionalOutput']
        optional_lo = [(line, id, vias) for ((line, col), (id, vias)) in
                       optional]
        labels = annotations['Label']
        labels_dict = {key: value for (key, value) in labels}
        try:
            translate(path, jvm)
            assert False
        except InvalidProgramException as e1:
            code = 'invalid.program:' + e1.code
            line = e1.node.lineno
            actual = [(line, code, [])]
        except TypeException as e2:
            actual = [self.extract_mypy_error(msg) for msg in e2.messages if
                      mypy_error_matcher.match(msg)]

        self.compare_actual_expected(actual, expected_lo, optional_lo, {})


translation_tester = TranslationTests()


def translation_test_files():
    return _test_files(test_translation_dir)


@pytest.mark.parametrize('path', translation_test_files())
def test_translation(path):
    translation_tester.test_file(path, jvm)


def sif_test_files():
    files = _test_files(test_sif_dir)
    result = []
    for file in files:
        result.extend([(file, verifier) for verifier in verifiers])
    return result


@pytest.mark.parametrize('path,verifier', sif_test_files())
def test_sif(path, verifier):
    verification_tester.test_file(path, jvm, verifier, True)



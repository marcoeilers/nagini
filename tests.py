import io
import jvmaccess
import os
import pytest
import tokenize

from main import translate, verify, get_mypy_dir
from os.path import isfile, join
from translator import InvalidProgramException
from typeinfo import TypeException
from typing import List, Tuple
from util import flatten
from verifier import VerificationResult

test_translation_dir = 'tests/translation/'
test_verification_dir = 'tests/verification/'
viperjar = os.environ['VIPERJAR']
mypydir = get_mypy_dir()
jvm = jvmaccess.JVM(viperjar)


class AnnotatedTests():
    def _is_annotation(self, tk: tokenize.TokenInfo) -> bool:
        """
        A test annotation is a comment starting with #::
        """
        return (tk.type is tokenize.COMMENT
                and tk.string.strip().startswith('#:: ')
                and tk.string.strip().endswith(')'))

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

    def test_file(self, path: str):
        prog = translate(path, jvm, mypydir)
        assert prog is not None
        vresult = verify(prog, path, jvm)
        self.evaluate_result(vresult, path, jvm)

    def token_to_expected(self, token):
        content = token.string.strip()[4:]
        strippedlist = content.split(';')
        return [(token.start, stripped[15:len(stripped) - 1]) for stripped in
                strippedlist]

    def failure_to_actual(self, error: 'silver.verifier.AbstractError') \
            -> Tuple[int, int, str, str]:
        return ((error.pos().line(), error.pos().column()), error.fullId(),
                error.readableMessage())

    def compare_actual_expected(self, actual, expected):
        actual_unexpected = []
        missing_expected = []
        for ae in actual:
            (line, id) = ae
            if not (line - 1, id) in expected:
                actual_unexpected += [ae]
        for ee in expected:
            (line, id) = ee
            if not (line + 1, id) in actual:
                missing_expected += [ee]
        assert not actual_unexpected
        assert not missing_expected


class VerificationTests(AnnotatedTests):
    def evaluate_result(self, vresult: VerificationResult, file_path: str,
                        jvm: jvmaccess.JVM):
        """
        Evaluates the verification result w.r.t. the test annotations in
        the file
        """
        test_annotations = self.get_test_annotations(file_path)
        expected = flatten(
            [self.token_to_expected(ann) for ann in test_annotations if
             ann.string.strip().startswith('#:: ExpectedOutput(')])
        expected_lo = [(line, id) for ((line, col), id) in expected]
        if vresult:
            assert not expected
        else:
            missing_info = [error for error in vresult.errors if
                            not isinstance(error.pos(),
                                           jvm.viper.silver.ast.HasLineColumn)]
            actual = [self.failure_to_actual(error) for error in vresult.errors
                      if not error in missing_info]
            actual_lo = [(line, id) for ((line, col), id, msg) in actual]
            assert not missing_info
            self.compare_actual_expected(actual_lo, expected_lo)


verification_tester = VerificationTests()


def verification_test_files():
    result = []
    for f in os.listdir(test_verification_dir):
        joined = join(test_verification_dir, f)
        if isfile(joined) and f.endswith('.py'):
            result.append(joined)
    return result


@pytest.mark.parametrize('path', verification_test_files())
def test_verification(path):
    verification_tester.test_file(path)


class TranslationTests(AnnotatedTests):
    def extract_mypy_error(self, message):
        start = message.index(', line ') + 7
        parts = message[start:].split(':', 1)
        return (int(parts[0]), 'type.error:' + parts[1].strip())

    def test_file(self, path: str):
        test_annotations = self.get_test_annotations(path)
        expected = flatten(
            [self.token_to_expected(ann) for ann in test_annotations if
             ann.string.strip().startswith('#:: ExpectedOutput(')])
        expected_lo = [(line, id) for ((line, col), id) in expected]
        try:
            translate(path, jvm, mypydir)
            assert False
        except InvalidProgramException as e1:
            code = 'invalid.program:' + e1.code
            line = e1.node.lineno
            actual = [(line, code)]
        except TypeException as e2:
            actual = [self.extract_mypy_error(msg) for msg in e2.messages if
                      ', line ' in msg]

        self.compare_actual_expected(actual, expected_lo)


translation_tester = TranslationTests()


def translation_test_files():
    test_files = [join(test_translation_dir, f) for f in
                  os.listdir(test_translation_dir) if
                  isfile(join(test_translation_dir, f)) and f.endswith(
                      '.py')]
    return test_files


@pytest.mark.parametrize('path', translation_test_files())
def test_translation(path):
    translation_tester.test_file(path)

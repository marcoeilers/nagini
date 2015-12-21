import io
import jvmaccess
import os
import tokenize
import unittest

from main import translate, verify, get_mypy_dir
from os.path import isfile, join
from typing import List, Tuple
from verifier import VerificationResult

test_translation_dir = 'tests/translation/'
test_verification_dir = 'tests/verification/'
viperjar = os.environ['VIPERJAR']
mypydir = get_mypy_dir()
jvm = jvmaccess.JVM(viperjar)


class VerificationTests(unittest.TestCase):
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

    def _test_file(self, path: str):
        prog = translate(path, jvm, mypydir)
        self.assertIsNotNone(prog)
        vresult = verify(prog, path, jvm)
        self.evaluate_result(vresult, path, jvm)

    def _get_py_files(self):
        result = []
        for f in os.listdir(test_verification_dir):
            joined = join(test_verification_dir, f)
            if isfile(joined) and f.endswith('.py'):
                result.append(joined)
        return result

    def test_verification(self):
        test_files = self._get_py_files()
        for f in test_files:
            with self.subTest(i=str(f)):
                self._test_file(f)

    def token_to_expected(self, token):
        stripped = token.string.strip()
        return (token.start, stripped[19:len(stripped) - 1])

    def failure_to_actual(self, error: 'silver.verifier.AbstractError') \
            -> Tuple[int, int, str, str]:
        return ((error.pos().line(), error.pos().column()), error.fullId(),
                error.readableMessage())

    def evaluate_result(self, vresult: VerificationResult, file_path: str,
                        jvm: jvmaccess.JVM):
        """
        Evaluates the verification result w.r.t. the test annotations in
        the file
        """
        test_annotations = self.get_test_annotations(file_path)
        expected = [self.token_to_expected(ann) for ann in test_annotations if
                    ann.string.strip().startswith('#:: ExpectedOutput(')]
        expected_lo = [(line, id) for ((line, col), id) in expected]
        if vresult:
            self.assertFalse(expected)
        else:
            missing_info = [error for error in vresult.errors if
                            not isinstance(error.pos(),
                                           jvm.viper.silver.ast.HasLineColumn)]
            actual = [self.failure_to_actual(error) for error in vresult.errors
                      if not error in missing_info]
            actual_lo = [(line, id) for ((line, col), id, msg) in actual]
            self.assertFalse(missing_info)
            actual_unexpected = []
            missing_expected = []
            for ae in actual:
                ((line, col), id, msg) = ae
                if not (line - 1, id) in expected_lo:
                    actual_unexpected += [ae]
            for ee in expected:
                ((line, col), id) = ee
                if not (line + 1, id) in actual_lo:
                    missing_expected += [ee]
            self.assertFalse(actual_unexpected)
            self.assertFalse(missing_expected)


class TranslationTests(unittest.TestCase):
    def compare_translation(self, sil_path: str, py_path: str,
                            jvm: jvmaccess.JVM, mypydir: str):
        prog = translate(py_path, jvm, mypydir)
        parser = getattr(getattr(jvm.viper.silver.parser, "Parser$"), "MODULE$")
        with open(sil_path, 'r') as file:
            text = file.read()
        parsed = parser.parse(text, None)
        self.assertTrue(
            isinstance(parsed, getattr(jvm.scala.util.parsing.combinator,
                                       'Parsers$Success')))
        resolver = jvm.viper.silver.parser.Resolver(parsed.result())
        resolved = resolver.run()
        resolved = resolved.get()
        translator = jvm.viper.silver.parser.Translator(resolved)
        program = translator.translate()
        self.assertEquals(prog.toString(), program.get().toString())

    def _test_file(self, path: str):
        if not path.endswith('.py'):
            raise ValueError("Path does not specify a .py file.")
        sil_path = path[:len(path) - 3] + '.sil'
        self.compare_translation(sil_path, path, jvm, mypydir)

    def test_translation(self):
        test_files = [join(test_translation_dir, f) for f in
                      os.listdir(test_translation_dir) if
                      isfile(join(test_translation_dir, f)) and f.endswith(
                          '.py')]
        for f in test_files:
            with self.subTest(i=str(f)):
                self._test_file(f)


if __name__ == '__main__':
    unittest.main()

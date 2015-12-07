import unittest
import jvmaccess
import tokenize
import io
from os import listdir
from os.path import isfile, join
from main import translate, verify

test_translation_dir = 'tests/translation/'
test_verification_dir = 'tests/verification/'
viperjar = '/viper/git/silicon_qp/target/scala-2.11/silicon-quantified-permissions.jar'
mypydir = '/home/marco/.local/bin/mypy'
jvm = jvmaccess.JVM(viperjar)


class VerificationTests(unittest.TestCase):

    def get_test_annotations(self, path):
        """
        Retrieves test annotations from the given Python source file
        :param path:
        :return:
        """
        file = open(path, 'r')
        text = file.read()
        file.close()
        filebytes = io.BytesIO(bytes(text, 'utf-8'))
        tokens = tokenize.tokenize(filebytes.readline)
        test_annotations = [tk for tk in tokens if
                            tk.type is tokenize.COMMENT and tk.string.strip().startswith(
                                '#:: ') and tk.string.strip().endswith(')')]
        return test_annotations

    def _test_file(self, path):
        prog = translate(path, jvm, mypydir)
        self.assertIsNotNone(prog)
        vresult = verify(prog, path, jvm)
        self.evaluate_result(vresult, path, jvm)

    def test_all(self):
        test_files = [join(test_verification_dir, f) for f in listdir(test_verification_dir) if isfile(join(test_verification_dir, f)) and f.endswith('.py')]
        for f in test_files:
            with self.subTest(i=str(f)):
                self._test_file(f)

    def token_to_expected(self, token):
        stripped = token.string.strip()
        return (token.start, stripped[19:len(stripped) - 1])


    def failure_to_actual(self, error):
        return ((error.pos().line(), error.pos().column()), error.fullId(),
                 error.readableMessage())


    def evaluate_result(self, vresult, file_path, jvm):
        """
        Evaluates the verification result w.r.t. the test annotations in the file
        :param vresult:
        :param file_path:
        :param jvm:
        :return:
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
            actual = [self.failure_to_actual(error) for error in vresult.errors if
                      not error in missing_info]
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

    def compare_translation(self, sil_path, py_path, jvm, mypydir):
        prog = translate(py_path, jvm, mypydir)
        parser = getattr(getattr(jvm.viper.silver.parser, "Parser$"), "MODULE$")
        file = open(sil_path, 'r')
        text = file.read()
        file.close()
        parsed = parser.parse(text, None)
        self.assertTrue(isinstance(parsed, getattr(jvm.scala.util.parsing.combinator,
                                  'Parsers$Success')))
        resolver = jvm.viper.silver.parser.Resolver(parsed.result())
        resolved = resolver.run()
        resolved = resolved.get()
        translator = jvm.viper.silver.parser.Translator(resolved)
        # consistency = getattr(getattr(jvm.viper.silver.ast.utility, 'Consistency$'), 'MODULE$')
        program = translator.translate()
        self.assertEquals(prog.toString(), program.get().toString())

    def _test_file(self, path):
        if not path.endswith('.py'):
            raise Exception()
        sil_path = path[:len(path) - 3] + '.sil'
        self.compare_translation(sil_path, path, jvm, mypydir)

    def test_all(self):
        test_files = [join(test_translation_dir, f) for f in listdir(test_translation_dir) if isfile(join(test_translation_dir, f)) and f.endswith('.py')]
        for f in test_files:
            with self.subTest(i=str(f)):
                self._test_file(f)


if __name__ == '__main__':
    unittest.main()

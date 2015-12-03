import io
import tokenize


def print_missing_expected(errors):
    print("Missing expected errors:")
    print(errors)


def print_actual_unexpected(errors):
    print("Actual unexpected errors:")
    print(errors)


def print_missing_info(errors):
    print("Errors with incomplete information:")
    print(errors)


def token_to_expected(token):
    stripped = token.string.strip()
    return (token.start, stripped[19:len(stripped) - 1])


def failure_to_actual(error):
    return ((error.pos().line(), error.pos().column()), error.fullId(),
            error.readableMessage())


def evaluate_result(vresult, file_path, jvm):
    """
    Evaluates the verification result w.r.t. the test annotations in the file
    :param vresult:
    :param file_path:
    :param jvm:
    :return:
    """
    test_annotations = get_test_annotations(file_path)
    expected = [token_to_expected(ann) for ann in test_annotations if
                ann.string.strip().startswith('#:: ExpectedOutput(')]
    expected_lo = [(line, id) for ((line, col), id) in expected]
    if vresult:
        if len(expected) > 0:
            print_missing_expected(expected)
        else:
            print("Test passed with no errors.")
    else:
        missing_info = [error for error in vresult.errors if
                        not isinstance(error.pos(),
                                       jvm.viper.silver.ast.HasLineColumn)]
        actual = [failure_to_actual(error) for error in vresult.errors if
                  not error in missing_info]
        actual_lo = [(line, id) for ((line, col), id, msg) in actual]
        if missing_info:
            print_missing_info(missing_info)
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
        anything_wrong = False
        if actual_unexpected:
            anything_wrong = True
            print_actual_unexpected(actual_unexpected)
        if missing_expected:
            anything_wrong = True
            print_missing_expected(missing_expected)
        if not anything_wrong:
            print("Test passed with expected errors.")


def get_test_annotations(path):
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

"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Nagini tests based on pytest framework.

Nagini tests are based on ideas taken from ``Silver``. Each test is a
Python source file with annotations that specify the expected behaviour.
The goal of the test suite is to catch changes in the behaviour,
therefore, annotations must be always up-to-date. Annotations are
written in Python comments that start with ``::``. Multiple annotations
on the same line are separated by ``|``.

Supported annotation types are:

1.  ``ExpectedOutput<(backend)>(<error_id>, <via1>, <via2>,…)`` –
    indicates that the following line should produce the specified
    error.
2.  ``UnexpectedOutput<(backend)>(<error_id>, <issue>, <via1>, <via2>,…)``
    – indicates that the following line should not produce the
    specified error, but it currently does. The problem is currently
    tracked in ``backend`` (if missing, then Nagini) issue tracker's
    issue ``issue``.
3.  ``MissingOutput<(backend)>(<error_id>, <issue>, <via1>, <via2>,…)`` –
    indicates that the error mentioned in the matching
    ``ExpectedOutput`` annotation is not produced due to issue
    ``issue``.
4.  ``Label(via)`` – mark location to be used in other annotations.
5.  ``IgnoreFile(<issue>)`` – mark that file cannot be tested due to
    critical issue such as a crash, which is tracked in ``issue``.
"""


import abc
import os
import pytest
import re
import tokenize
from collections import Counter
from typing import Any, Dict, List, Optional


from nagini_translation.lib import config, jvmaccess
from nagini_translation.lib.errors import error_manager
from nagini_translation.lib.typeinfo import TypeException
from nagini_translation.lib.util import InvalidProgramException
from nagini_translation.main import translate, verify, TYPE_ERROR_PATTERN
from nagini_translation.verifier import VerificationResult, ViperVerifier


_JVM = jvmaccess.JVM(config.classpath)


_MYPY_ERROR_MATCHER = re.compile(TYPE_ERROR_PATTERN)

_BACKEND_SILICON = 'silicon'
_BACKEND_CARBON = 'carbon'
_BACKEND_ANY = 'ANY'


def _consume(key: str, dictionary: Dict[str, Any], check: bool = False) -> Any:
    """Destructive read from the dictionary.

    If ``check`` is ``True``, check that read value does not evaluate to
    ``false``.
    """
    value = dictionary[key]
    del dictionary[key]
    if check:
        assert value, "{} in {} is False".format(key, dictionary)
    return value


def _consume_list(key: str, dictionary: Dict[str, Any]) -> Any:
    """Destructive read of comma separated list from the dictionary."""
    value = _consume(key, dictionary)
    if value:
        return [part for part in value.split(',') if part]
    else:
        return []


class Error(abc.ABC):
    """Base class for reported errors.

    Subclasses of this class are wrappers that unify interfaces of three
    error types currently produced by Nagini:

    1.  Type errors produced by Mypy.
    2.  Invalid program errors produced by translators.
    3.  Verification errors produced by back-end verifiers.
    """

    @property
    @abc.abstractmethod
    def full_id(self) -> str:
        """Return full error id."""

    @property
    @abc.abstractmethod
    def line(self) -> int:
        """Return line number."""

    @abc.abstractmethod
    def get_vias(self) -> List[int]:
        """Return a list of vias."""


class VerificationError(Error):
    """Verification error reported by verifier."""

    def __init__(self, actual_error: 'Error') -> None:
        self._error = actual_error

    def __repr__(self) -> str:
        return 'VerificationError({}, line={}, vias={})'.format(
            self.full_id, self.line, self.get_vias())

    @property
    def full_id(self) -> str:
        return self._error.full_id

    @property
    def line(self) -> int:
        return self._error.position.line

    def get_vias(self) -> List[int]:
        reason_pos = self._error.reason.position
        if reason_pos.node_id:
            vias = error_manager.get_vias(reason_pos.node_id)
            if vias:
                return [via[1].line() for via in vias]
        error_pos = self._error.position
        if error_pos.node_id:
            vias = error_manager.get_vias(error_pos.node_id)
            return [via[1].line() for via in vias]
        return []


class InvalidProgramError(Error):
    """Invalid program error reported by translator."""

    def __init__(self, exception: InvalidProgramException) -> None:
        self._exception = exception

    def __repr__(self) -> str:
        return 'InvalidProgramError({}, line={}, vias={})'.format(
            self.full_id, self.line, self.get_vias())

    @property
    def full_id(self) -> str:
        return 'invalid.program:' + self._exception.code

    @property
    def line(self) -> int:
        return self._exception.node.lineno

    def get_vias(self) -> List[int]:
        return []


class TypeCheckError(Error):
    """Type error reported by Mypy."""

    def __init__(self, msg: str) -> None:
        self._msg = msg
        match = _MYPY_ERROR_MATCHER.match(msg)
        self._groups = match.groupdict()

    def __repr__(self) -> str:
        return 'TypeCheckError({}, line={}, vias={})'.format(
            self.full_id, self.line, self.get_vias())

    @property
    def full_id(self) -> str:
        return 'type.error:' + self._groups['msg']

    @property
    def line(self) -> int:
        return int(self._groups['line'])

    def get_vias(self) -> List[int]:
        return []


class Annotation:
    """Base class for all test annotations."""

    def __init__(
            self, token: tokenize.TokenInfo,
            group_dict: Dict[str, Optional[str]]) -> None:
        self._token = token
        for key, value in group_dict.items():
            if key == 'type':
                continue
            if value:
                setter_name = '_set_' + key
                # Here we check that provided annotation does not have
                # too much stuff.
                assert hasattr(self, setter_name), (
                    "Unsupported {} for {}".format(value, self))
                getattr(self, setter_name)(value)

    @property
    def line(self) -> int:
        """Get line number of this annotation."""
        return self._token.start[0] + 1

    @property
    @abc.abstractmethod
    def backend(self) -> str:
        """Back-end which this annotation is targeting."""


class BackendSpecificAnnotationMixIn:
    """Annotation that depends on the back-end.

    The subclass is expected to define a field ``_backend``.
    """

    @property
    def backend(self) -> str:
        """Back-end which this annotation is targeting."""
        return self._backend or _BACKEND_ANY


class ErrorMatchingAnnotationMixIn:
    """An annotation that can match an error.

    The subclass is expected to define fields ``_id`` and ``_labels``.
    """

    def match(self, error: Error) -> bool:
        """Check is error matches this annotation."""
        return (self._id == error.full_id.replace(', ', '; ') and
                self.line == error.line and
                self.get_vias() == error.get_vias())


class UsingLabelsAnnotationMixIn:
    """An annotation that can refer to labels.

    The subclass is expected to define the field ``_labels``.
    """

    def resolve_labels(
            self, labels_dict: Dict[str, 'LabelAnnotation']) -> None:
        """Resolve label names to label objects."""
        for i, label in enumerate(self._labels):
            self._labels[i] = labels_dict[label]

    def get_vias(self) -> List[int]:
        """Return vias extracted from label positions."""
        return [label.line for label in self._labels]


class ExpectedOutputAnnotation(
        BackendSpecificAnnotationMixIn,
        ErrorMatchingAnnotationMixIn,
        UsingLabelsAnnotationMixIn,
        Annotation):
    """ExpectedOutput annotation."""

    def __init__(
            self, token: tokenize.TokenInfo,
            group_dict: Dict[str, Optional[str]]) -> None:
        """ExpectedOutput constructor.

        Supported info:

        +   id – mandatory.
        +   backend – optional.
        +   labels – optional.
        """
        self._id = _consume('id', group_dict, True)
        self._backend = _consume('backend', group_dict)
        self._labels = _consume_list('labels', group_dict)
        super().__init__(token, group_dict)

    def __repr__(self) -> str:
        return 'ExpectedOutput({}, line={}, vias={})'.format(
            self._id, self.line, self.get_vias())

    @property
    def full_id(self) -> str:
        """Return full error id."""
        return self._id


class UnexpectedOutputAnnotation(
        BackendSpecificAnnotationMixIn,
        ErrorMatchingAnnotationMixIn,
        UsingLabelsAnnotationMixIn,
        Annotation):
    """UnexpectedOutput annotation."""

    def __init__(
            self, token: tokenize.TokenInfo,
            group_dict: Dict[str, Optional[str]]) -> None:
        """UnexpectedOutput constructor.

        Supported info:

        +   id – mandatory.
        +   backend – optional, ``None`` means ``nagini``.
        +   issue_id – mandatory.
        +   labels – optional.
        """
        self._id = _consume('id', group_dict, True)
        self._backend = _consume('backend', group_dict)
        self._issue_id = _consume('issue_id', group_dict, True)
        self._labels = _consume_list('labels', group_dict)
        super().__init__(token, group_dict)

    def __repr__(self) -> str:
        return 'UnexpectedOutput({}, line={}, vias={})'.format(
            self._id, self.line, self.get_vias())


class MissingOutputAnnotation(
        BackendSpecificAnnotationMixIn,
        UsingLabelsAnnotationMixIn,
        Annotation):
    """MissingOutput annotation."""

    def __init__(
            self, token: tokenize.TokenInfo,
            group_dict: Dict[str, Optional[str]]) -> None:
        """MissingOutput constructor.

        Supported info:

        +   id – mandatory.
        +   backend – optional, ``None`` means ``nagini``.
        +   issue_id – mandatory.
        +   labels – optional.
        """
        self._id = _consume('id', group_dict, True)
        self._backend = _consume('backend', group_dict)
        self._issue_id = _consume('issue_id', group_dict, True)
        self._labels = _consume_list('labels', group_dict)
        super().__init__(token, group_dict)

    def match(self, expected: ExpectedOutputAnnotation) -> bool:
        """Check if this annotation matches the given ``ExpectedOutput``.

        ``MissingOutput`` annotation indicates that the output mentioned
        in a certain ``ExpectedOutput`` annotation is not going to be
        produced due to some issue. In other words, a ``MissingOutput``
        annotation silences a matching ``ExpectedOutput`` annotation.
        Intuitively, a ``MissingOutput`` annotation matches an
        ``ExpectedOutput`` annotation if they are on the same line and
        have the same arguments.
        """
        return (self.line == expected.line and
                self._id == expected.full_id and
                self.get_vias() == expected.get_vias() and
                (self.backend == expected.backend or
                 self.backend == _BACKEND_ANY or
                 expected.backend == _BACKEND_ANY))


class LabelAnnotation(Annotation):
    """Label annotation."""

    def __init__(
            self, token: tokenize.TokenInfo,
            group_dict: Dict[str, Optional[str]]) -> None:
        """Label constructor.

        Supported info:

        +   id – mandatory.
        """
        self._id = _consume('id', group_dict, True)
        super().__init__(token, group_dict)

    @property
    def name(self) -> str:
        """Return the labels name."""
        return self._id

    @property
    def backend(self) -> str:
        """Back-end which this annotation is targeting."""
        return _BACKEND_ANY


class IgnoreFileAnnotation(
        BackendSpecificAnnotationMixIn,
        Annotation):
    """IgnoreFile annotation."""

    def __init__(
            self, token: tokenize.TokenInfo,
            group_dict: Dict[str, Optional[str]]) -> None:
        """IgnoreFile constructor.

        Supported info:

        +   id – mandatory, used as issue_id.
        +   backend – optional, ``None`` means ``nagini``.
        """
        self._issue_id = _consume('id', group_dict, True)
        assert self._issue_id.isnumeric(), "Issue id must be a number."
        self._backend = _consume('backend', group_dict)
        super().__init__(token, group_dict)


class AnnotationManager:
    """A class for managing annotations in the specific test file."""

    def __init__(self, backend: str) -> None:
        self._matcher = re.compile(
            # Annotation type such as ExpectedOutput.
            r'(?P<type>[a-zA-Z]+)'
            # To which back-end the annotation is dedicated. None means
            # both.
            r'(\((?P<backend>[a-z]+)\))?'
            r'\('
            # Error message, or label id. Matches everything except
            # comma.
            r'(?P<id>[a-zA-Z\.\(\)_\[\]\-:;\d ?\'"]+)'
            # Issue id in the issue tracker.
            r'(,(?P<issue_id>\d+))?'
            # Labels. Note that label must start with a letter.
            r'(?P<labels>(,[a-zA-Z][a-zA-Z\d_]+)+)?'
            r'\)'
        )
        self._annotations = {
            'ExpectedOutput': [],
            'UnexpectedOutput': [],
            'MissingOutput': [],
            'Label': [],
            'IgnoreFile': [],
        }
        self._backend = backend

    def _create_annotation(
            self, annotation_string: str, token: tokenize.TokenInfo) -> None:
        """Create annotation object from the ``annotation_string``."""
        match = self._matcher.match(annotation_string)
        assert match, "Failed to match: {}".format(annotation_string)
        group_dict = match.groupdict()
        annotation_type = group_dict['type']
        if annotation_type == 'ExpectedOutput':
            annotation = ExpectedOutputAnnotation(token, group_dict)
        elif annotation_type == 'UnexpectedOutput':
            annotation = UnexpectedOutputAnnotation(token, group_dict)
        elif annotation_type == 'MissingOutput':
            annotation = MissingOutputAnnotation(token, group_dict)
        elif annotation_type == 'Label':
            annotation = LabelAnnotation(token, group_dict)
        elif annotation_type == 'IgnoreFile':
            annotation = IgnoreFileAnnotation(token, group_dict)
        else:
            assert False, "Unknown annotation type: {}".format(annotation_type)
        assert annotation_type in self._annotations
        if annotation.backend in (self._backend, _BACKEND_ANY):
            self._annotations[annotation_type].append(annotation)

    def _get_expected_output(self) -> List[ExpectedOutputAnnotation]:
        """Return a final list of expected output annotations."""
        expected_annotations = self._annotations['ExpectedOutput']
        missing_annotations = set(self._annotations['MissingOutput'])
        # Filter out annotations that should be missing.
        annotations = []
        for expected in expected_annotations:
            for missing in missing_annotations:
                if missing.match(expected):
                    missing_annotations.remove(missing)
                    break
            else:
                annotations.append(expected)
        assert not missing_annotations
        # Append unexpected annotations.
        annotations.extend(self._annotations['UnexpectedOutput'])
        return annotations

    def resolve_references(self) -> None:
        """Resolve references to labels."""
        labels_dict = dict(
            (label.name, label)
            for label in self._annotations['Label'])
        for annotation_type in ['ExpectedOutput', 'UnexpectedOutput',
                                'MissingOutput']:
            for annotation in self._annotations[annotation_type]:
                annotation.resolve_labels(labels_dict)

    def check_errors(self, actual_errors: List[Error]) -> None:
        """Check if actual errors match annotations."""
        annotations = set(self._get_expected_output())
        unexpected_errors = []
        for error in actual_errors:
            for annotation in annotations:
                if annotation.match(error):
                    annotations.remove(annotation)
                    break
            else:
                unexpected_errors.append(error)
        if unexpected_errors:
            print(unexpected_errors)
            assert False
        if annotations:
            print(annotations)
            assert False

    def has_unexpected_missing(self) -> bool:
        """Check if there are unexpected or missing output annotations."""
        return (self._annotations['UnexpectedOutput'] or
                self._annotations['MissingOutput'])

    def extract_annotations(self, token: tokenize.TokenInfo) -> None:
        """Extract annotations mentioned in the token."""
        content = token.string.strip()[3:]
        stripped_list = [part.strip() for part in content.split('|')]
        for part in stripped_list:
            self._create_annotation(part, token)

    def ignore_file(self) -> bool:
        """Check if file should be ignored."""
        return bool(self._annotations['IgnoreFile'])


class AnnotatedTest:
    """A class representing an annotated test.

    An annotated test is a Python source file with annotations that
    indicate expected verification errors.
    """

    def _is_annotation(self, token: tokenize.TokenInfo) -> bool:
        """Check if token is a test annotation.

        A test annotation is a comment starting with ``#::``.
        """
        return (token.type is tokenize.COMMENT and
                token.string.strip().startswith('#:: ') and
                token.string.strip().endswith(')'))

    def get_annotation_manager(
            self, path: str, backend: str) -> AnnotationManager:
        """Create ``AnnotationManager`` for given Python source file."""
        manager = AnnotationManager(backend)
        with open(path, 'rb') as fp:
            for token in tokenize.tokenize(fp.readline):
                if self._is_annotation(token):
                    manager.extract_annotations(token)
        manager.resolve_references()
        return manager


class VerificationTest(AnnotatedTest):
    """Test for testing verification of successfully translated programs."""

    def test_file(
            self, path: str, base: str, jvm: jvmaccess.JVM, verifier: ViperVerifier,
            sif: bool, reload_resources: bool, arp: bool, ignore_obligations: bool, store_viper: bool):
        """Test specific Python file."""
        config.obligation_config.disable_all = ignore_obligations
        annotation_manager = self.get_annotation_manager(path, verifier.name)
        if arp:
            pytest.skip('Ignoring ARP tests')
        if annotation_manager.ignore_file():
            pytest.skip('Ignored')
        abspath = os.path.abspath(path)
        absbase = os.path.abspath(base)
        modules, prog = translate(abspath, jvm, base_dir=absbase, sif=sif, arp=arp, reload_resources=reload_resources)
        assert prog is not None
        if store_viper:
            import string
            valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
            file_name = "".join(x for x in path if x in valid_chars) + '.vpr'
            dir = 'viper_out'
            if not os.path.exists(dir):
                os.makedirs(dir)
            file_path = os.path.join(dir, file_name)
            with open(file_path, 'w') as fp:
                fp.write(str(prog))
        enable_ce = verifier == ViperVerifier.silicon and not sif
        vresult = verify(modules, prog, abspath, jvm, verifier, arp=arp, counterexample=enable_ce)
        self._evaluate_result(vresult, annotation_manager, jvm, sif)

    def _evaluate_result(
            self, vresult: VerificationResult,
            annotation_manager: AnnotationManager, jvm: jvmaccess.JVM, sif: bool = False):
        """Evaluate verification result with regard to test annotations."""
        if vresult:
            actual_errors = []
        else:
            assert all(
                isinstance(error.pos(), jvm.viper.silver.ast.HasLineColumn)
                for error in vresult.errors)
            actual_errors = [
                VerificationError(error) for error in vresult.errors]
            if sif:
                # carbon will report all functional errors twice, as we model two
                # executions, therefore we filter duplicated errors here.
                # (Note: we don't make errors unique, just remove one duplicate)
                distinct = []
                reprs = map(lambda e: e.__repr__(), actual_errors)
                repr_counts = Counter(reprs)
                repr_counts = dict(map(lambda rc: (rc[0], -(-rc[1] // 2)),
                                       repr_counts.items()))
                for err in actual_errors:
                    if repr_counts[err.__repr__()] > 0:
                        distinct.append(err)
                        repr_counts[err.__repr__()] -= 1
                actual_errors = distinct
        annotation_manager.check_errors(actual_errors)
        if annotation_manager.has_unexpected_missing():
            pytest.skip('Unexpected or missing output')


_VERIFICATION_TESTER = VerificationTest()


def test_verification(path, base, verifier, sif, reload_resources, arp, ignore_obligations, print):
    """Execute provided verification test."""
    _VERIFICATION_TESTER.test_file(path, base, _JVM, verifier, sif, reload_resources, arp, ignore_obligations, print)


class TranslationTest(AnnotatedTest):
    """Test for testing translation errors."""

    def test_file(self, path: str, base: str, jvm: jvmaccess.JVM, sif: bool,
                  reload_resources: bool, arp: bool):
        """Test specific Python file."""
        annotation_manager = self.get_annotation_manager(path, _BACKEND_ANY)
        if annotation_manager.ignore_file():
            pytest.skip('Ignored')
        path = os.path.abspath(path)
        base = os.path.abspath(base)
        try:
            translate(path, jvm, base_dir=base, sif=sif, arp=arp, reload_resources=reload_resources)
            actual_errors = []
        except InvalidProgramException as exp1:
            actual_errors = [InvalidProgramError(exp1)]
        except TypeException as exp2:
            actual_errors = [
                TypeCheckError(msg) for msg in exp2.messages
                if _MYPY_ERROR_MATCHER.match(msg)]
        annotation_manager.check_errors(actual_errors)
        if annotation_manager.has_unexpected_missing():
            pytest.skip('Unexpected or missing output')


_TRANSLATION_TESTER = TranslationTest()


def test_translation(path, base, sif, reload_resources, arp):
    """Execute provided translation test."""
    _TRANSLATION_TESTER.test_file(path, base, _JVM, sif, reload_resources, arp)

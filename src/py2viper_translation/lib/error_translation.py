"""Helper classes for translating Viper errors to py2viper errors."""


from typing import List, Dict, Type         # pylint: disable=unused-import

# Just to make mypy happy.
if False:                                   # pylint: disable=using-constant-test
    from viper.silver import ast            # pylint: disable=import-error,unused-import,wrong-import-order
    from viper.silver.verifier import (     # pylint: disable=import-error,unused-import
        AbstractVerificationError,
        AbstractErrorReason,
    )


class BaseError:
    """Wrapper around ``AbstractVerificationError``."""

    def __init__(self, error: 'AbstractVerificationError') -> None:
        self._error = error     # Original error.

    def pos(self) -> 'ast.IdentifierPosition':
        """Error position."""
        return self._error.pos()

    def fullId(self) -> str:                # pylint: disable=invalid-name
        """Full error identifier."""
        return self._error.fullId()

    def reason(self) -> 'AbstractErrorReason':
        """Error reason."""
        return self._error.reason()

    def offendingNode(self) -> 'ast.Node':  # pylint: disable=invalid-name
        """AST node where the error occurred."""
        return self._error.offendingNode()

    def readableMessage(self) -> str:       # pylint: disable=invalid-name
        """Readable error message."""
        return self._error.readableMessage()


class TerminationMeasureError(BaseError):
    """Termination measure is not well-formed."""

    def fullId(self):
        """Full error identifier.

        Return measure non-positive identifier instead of assertion
        failure.
        """
        original_id = super().fullId()
        if original_id == 'assert.failed:assertion.false':
            return 'termination_check.failed:measure.non_positive'
        else:
            return original_id


class ErrorTranslationManager:
    """A singleton object that manages error translation."""

    def __init__(self) -> None:
        self._translators = {}  # type: Dict[str, Type[BaseError]]

    def translate(
            self,
            errors: List['AbstractVerificationError']) -> List[BaseError]:
        """Wrap Viper errors into py2viper errors."""
        translated_errors = [
            self._translate_error(error)
            for error in errors
        ]
        return translated_errors

    def _translate_error(
            self, error: 'AbstractVerificationError') -> BaseError:
        node_id = error.pos().id()
        if node_id in self._translators:
            return self._translators[node_id](error)
        else:
            return BaseError(error)

    def register_translator(self, node_id: str,
                            error_translator: Type[BaseError]) -> None:
        """Register an error translator.

        Error translator is a ``BaseError`` subclass that is used to
        wrap Viper errors at position with ``id=node_id``.
        """
        assert node_id not in self._translators
        self._translators[node_id] = error_translator


manager = ErrorTranslationManager()     # pylint: disable=invalid-name

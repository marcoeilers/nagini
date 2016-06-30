import ast
import astunparse

from abc import ABCMeta
from enum import Enum
from py2viper_translation.lib import config
from py2viper_translation.lib.cache import cache
from py2viper_translation.lib.jvmaccess import JVM


class ViperVerifier(Enum):
    silicon = 'silicon'
    carbon = 'carbon'


class VerificationResult(metaclass=ABCMeta):
    pass


class Success(VerificationResult):
    """
    Encodes a verification success
    """

    def __bool__(self):
        return True

    def __str__(self):
        return "Verification successful."


def pprint(node):
    if not node:
        raise ValueError(node)
    if isinstance(node, str):
        return node
    if isinstance(node, ast.FunctionDef):
        # FIXME: just for debugging, whenever this happens it's almost certainly
        # wrong.
        raise ValueError(node)
    res = astunparse.unparse(node)
    res = res.replace('\n', '')
    return res


def get_target_name(node: ast.AST) -> str:
    if (not isinstance(node, ast.Call) and
            not isinstance(node, ast.FunctionDef)):
        node = get_containing_member(node)
    if isinstance(node, ast.FunctionDef):
        return node.name
    func = node.func
    if isinstance(func, ast.Name):
        func = func.id
    if isinstance(func, ast.Attribute):
        func = func.attr
    return func


def get_containing_member(node: ast.AST):
    member = node
    while not isinstance(member, ast.FunctionDef) and member is not None:
        if hasattr(member, '_parent'):
            member = member._parent
        else:
            member = None
    return member


errors = {
    'assignment.failed': lambda n: 'Assignment might fail.',
    'call.failed': lambda n: 'Method call might fail.',
    'not.wellformed': lambda n: 'Contract might not be well-formed.',
    'call.precondition':
        lambda n: 'The precondition of method ' + get_target_name(n) + ' might not hold.',
    'application.precondition':
        lambda n: 'Precondition of function ' + get_target_name(n) + ' might not hold.',
    'exhale.failed': lambda n: 'Exhale might fail.',
    'inhale.failed': lambda n: 'Inhale might fail.',
    'if.failed': lambda n: 'Conditional statement might fail.',
    'while.failed': lambda n: 'While statement might fail.',
    'assert.failed': lambda n: 'Assert might fail.',
    'postcondition.violated':
        lambda n: 'Postcondition of ' + get_containing_member(n).name + ' might not hold.',
    'fold.failed': lambda n: 'Fold might fail.',
    'unfold.failed': lambda n: 'Unfold might fail.',
    'invariant.not.preserved':
        lambda n: 'Loop invariant might not be preserved.',
    'invariant.not.established':
        lambda n: 'Loop invariant might not hold on entry.',
    'function.not.wellformed':
        lambda n: 'Function ' + get_containing_member(n).name + ' might not be well-formed.',
    'predicate.not.wellformed':
        lambda n: 'Predicate ' + get_containing_member(n).name + ' might not be well-formed.',
}

reasons = {
    'assertion.false': lambda n: 'Assertion ' + pprint(n) + ' might not hold.',
    'receiver.null': lambda n: 'Receiver of ' + pprint(n) + ' might be null.',
    'division.by.zero': lambda n: 'Divisor ' + pprint(n) + ' might be zero.',
    'negative.permission':
        lambda n: 'Fraction ' + pprint(n) + ' might be negative.',
    'insufficient.permission':
        lambda n: 'There might be insufficient permission to access ' + pprint(n) + '.',
}


class Failure(VerificationResult):
    """
    Encodes a verification failure and provides access to the errors
    """

    def __init__(self, errors: 'silver.verifier.AbstractError'):
        self.errors = errors

    def __bool__(self):
        return False

    def __str__(self):
        all_errors = [self.error_msg(error) for error in self.errors]
        return "Verification failed.\nErrors:\n" + '\n'.join(
            all_errors)

    def error_msg(self, error) -> str:
        pos_string = str(error.pos())
        got_proper_position = False
        error_id = error.fullId().split(':')
        reason_ = error.reason()
        reason_offending = error.reason().offendingNode()
        reason_pos = error.reason().offendingNode().pos()
        reason_string = None
        if hasattr(reason_pos, 'id'):
            reason_pos = reason_pos.id()
            reason_entry = cache[reason_pos]
            reason_node = reason_entry[0]
            reason_string = reason_entry[2]
            if reason_entry[1]:
                got_proper_position = True
            for via in reason_entry[1]:
                pos_string += ', via ' + via[0] + ' at ' + str(via[1])
        else:
            reason_file = reason_pos.file()
            reason_node = None
        reason = reason_string if reason_string else reason_node
        if not reason:
            reason = str(reason_offending)
        reason_msg = reasons[error_id[1]](reason)
        error_pos = error.pos()
        if hasattr(error_pos, 'id'):
            error_pos = error_pos.id()
            error_entry = cache[error_pos]
            error_node = error_entry[0]
            if not got_proper_position:
                for via in error_entry[1]:
                    pos_string += ', via ' + via[0] + ' at ' + str(via[1])
        else:
            off = error.offendingNode()
            off_pos = off.pos()
            error_node = None
        error_msg = errors[error_id[0]](error_node)

        return error_msg + ' ' + reason_msg + ' (' + pos_string + ')'


class Silicon:
    """
    Provides access to the Silicon verifier
    """

    def __init__(self, jvm: JVM, filename: str):
        self.silver = jvm.viper.silver
        self.silicon = jvm.viper.silicon.Silicon()
        args = jvm.scala.collection.mutable.ArraySeq(3)
        args.update(0, '--z3Exe')
        args.update(1, config.z3_path)
        args.update(2, filename)
        self.silicon.parseCommandLine(args)
        self.silicon.start()
        self.ready = True

    def verify(self, prog: 'silver.ast.Program') -> VerificationResult:
        """
        Verifies the given program using Silicon
        """
        if not self.ready:
            self.silicon.restart()
        result = self.silicon.verify(prog)
        self.ready = False
        if isinstance(result, self.silver.verifier.Failure):
            it = result.errors().toIterator()
            errors = []
            while it.hasNext():
                errors += [it.next()]
            return Failure(errors)
        else:
            return Success()


class Carbon:
    """
    Provides access to the Carbon verifier
    """

    def __init__(self, jvm: JVM, filename: str):
        self.silver = jvm.viper.silver
        self.carbon = jvm.viper.carbon.CarbonVerifier()
        args = jvm.scala.collection.mutable.ArraySeq(5)
        args.update(0, '--boogieExe')
        args.update(1, config.boogie_path)
        args.update(2, '--z3Exe')
        args.update(3, config.z3_path)
        args.update(4, filename)
        self.carbon.parseCommandLine(args)
        self.carbon.config().initialize(None)
        self.carbon.start()
        self.ready = True

    def verify(self, prog: 'silver.ast.Program') -> VerificationResult:
        """
        Verifies the given program using Carbon
        """
        if not self.ready:
            self.carbon.restart()
        result = self.carbon.verify(prog)
        self.ready = False
        if isinstance(result, self.silver.verifier.Failure):
            it = result.errors().toIterator()
            errors = []
            while it.hasNext():
                errors += [it.next()]
            return Failure(errors)
        else:
            return Success()

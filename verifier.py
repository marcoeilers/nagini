from abc import ABCMeta

from jvmaccess import JVM


class VerificationResult(metaclass=ABCMeta):
    pass


class Success:
    """
    Encodes a verification success
    """

    def __bool__(self):
        return True

    def __str__(self):
        return "Verification successful."


VerificationResult.register(Success)


class Failure:
    """
    Encodes a verification failure and provides access to the errors
    """

    def __init__(self, errors: 'viper.silver.verifier.AbstractError'):
        self.errors = errors

    def __bool__(self):
        return False

    def __str__(self):
        return "Verification failed.\nErrors:\n" + '\n'.join(
            [str(error) for error in self.errors])


VerificationResult.register(Failure)


class Verifier:
    """
    Provides access to the Silicon verifier
    """

    def __init__(self, jvm: JVM, filename: str):
        self.silver = jvm.viper.silver
        self.silicon = jvm.viper.silicon.Silicon()
        args = jvm.scala.collection.mutable.ArraySeq(1)
        args.update(0, filename)
        self.silicon.parseCommandLine(args)
        self.silicon.start()
        self.ready = True

    def verify(self, prog: 'viper.silver.ast.Program') \
            -> VerificationResult:
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

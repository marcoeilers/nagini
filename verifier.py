
class Success:
    def __bool__(self):
        return True

    def __str__(self):
        return "Verification successful."

class Failure:
    def __init__(self, errors):
        self.errors = errors

    def __bool__(self):
        return False

    def __str__(self):
        return "Verification failed.\nErrors:\n" + '\n'.join([str(error) for error in self.errors])

class Verifier:
    """
    Provides access to the Silicon verifier
    """

    def __init__(self, jvm, filename):
        self.silver = jvm.viper.silver
        self.silicon = jvm.viper.silicon.Silicon()
        args = jvm.scala.collection.mutable.ArraySeq(1)
        args.update(0, filename)
        self.silicon.parseCommandLine(args)
        self.silicon.start()
        self.ready = True

    def verify(self, prog):
        """
        Verifies the given program using Silicon
        :param prog: a Viper Program
        :return: result of the verification
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

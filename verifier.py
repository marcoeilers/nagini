

class Verifier:
    def __init__(self, jpype, filename):
        self.silicon = jpype.viper.silicon.Silicon()
        args = jpype.scala.collection.mutable.ArraySeq(1)
        args.update(0, filename)
        self.silicon.parseCommandLine(args)
        self.silicon.start()
        self.ready = True

    def verify(self, prog):
        if not self.ready:
            self.silicon.restart()
        result = self.silicon.verify(prog)
        self.ready = False
        return result
import jpype


class JVM:
    """
    Encapsulates access to a JVM
    """

    def __init__(self, classpath):
        jpype.startJVM(jpype.getDefaultJVMPath(),
                       '-Djava.class.path=' + classpath)
        self.java = jpype.JPackage('java')
        self.scala = jpype.JPackage('scala')
        self.viper = jpype.JPackage('viper')

    def __del__(self):
        jpype.shutdownJVM()

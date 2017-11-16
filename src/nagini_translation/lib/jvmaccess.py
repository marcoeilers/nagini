import jpype


class JVM:
    """
    Encapsulates access to a JVM
    """

    def __init__(self, classpath: str):
        if not jpype.isJVMStarted():
            jpype.startJVM(jpype.getDefaultJVMPath(),
                           '-Djava.class.path=' + classpath, '-Xss128m')
        self.java = jpype.JPackage('java')
        self.scala = jpype.JPackage('scala')
        self.viper = jpype.JPackage('viper')
        self.fastparse = jpype.JPackage('fastparse')

    def get_proxy(self, supertype, instance):
        return jpype.JProxy(supertype, inst=instance)

from py2viper_translation.lib.context import Context


class SIFContext(Context):
    def __init__(self):
        super().__init__()
        self.use_prime = False

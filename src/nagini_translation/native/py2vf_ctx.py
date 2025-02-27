import nagini_translation.native.vf.vf as vf
class py2vf_context:
    def __init__(self, p: "py2vf_context" = None):
        self.context = dict()
        self.parent = p
        self.setup = []

    def __getitem__(self, key: str):
        if key in self.context:
            return self.context[key]
        elif self.parent:
            return self.parent[key]
        else:
            # raise KeyError(key)
            return None

    def __setitem__(self, key: str, value: vf.Value):
        self.context[key] = value
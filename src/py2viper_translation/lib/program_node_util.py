from typing import Dict, List, Tuple


class CombinedDict:
    """
    A combined view on the given list of dicts, that adds the possibility to
    filter and rename some keys. E.g. if names contains ('k1', 'k2') then
    getting 'k1' will try to retrieve the value for key 'k2' from (one of) the
    given dicts. Unless 'names' is empty, keys that do not occur in 'names'
    will be reported as not contained by this view.
    """
    def __init__(self, names: List[Tuple[str, str]], dicts: List[Dict]):
        self.dicts = dicts
        self.names = {}
        for name, as_name in names:
            new_name = as_name if as_name else name
            self.names[new_name] = name

    def __getitem__(self, item):
        key = item
        if self.names:
            if not key in self.names:
                raise KeyError(item)
            key = self.names[key]
        for d in self.dicts:
            if key in d:
                return d[key]
        raise KeyError(item)

    def __contains__(self, item):
        key = item
        if self.names:
            if not key in self.names:
                return False
            key = self.names[key]
        for d in self.dicts:
            if key in d:
                return True
        return False


class ModuleDictView:
    """
    A view of the given aspect (e.g. 'functions') of the given module with the
    given renamings.
    """
    def __init__(self, names: List[Tuple[str, str]], module: 'PythonModule',
                 field: str):
        self.names = names
        self.module = module
        self.field = field
        self._dict = None

    def initialize(self) -> None:
        """
        We do this lazily because included module information may not be
        complete when we create this object.
        """
        modules = self.module.get_included_modules(include_global=False)
        dicts = [getattr(m, self.field) for m in modules]
        self._dict = CombinedDict(self.names, dicts)

    def __contains__(self, item):
        if self._dict is None:
            self.initialize()
        return item in self._dict

    def __getitem__(self, item):
        if self._dict is None:
            self.initialize()
        return self._dict[item]

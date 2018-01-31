

def error(msg: str, *args: object) -> None: ...

def warning(msg: str, *args: object) -> None: ...

def debug(msg: str, *args: object) -> None: ...

def info(msg: str, *args: object) -> None: ...


CRITICAL = 50
FATAL = CRITICAL
ERROR = 40
WARNING = 30
WARN = WARNING
INFO = 20
DEBUG = 10
NOTSET = 0
from typing import TypeVar

#:: ExpectedOutput(invalid.program:covariant.type.var)
T = TypeVar('T', covariant=True)
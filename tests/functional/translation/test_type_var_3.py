from typing import TypeVar

#:: ExpectedOutput(invalid.program:contravariant.type.var)
T = TypeVar('T', contravariant=True)
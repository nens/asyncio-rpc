from dataclasses import dataclass


@dataclass
class Integer:
    """
    Dataclass wrapper around an integer value
    """
    value: int


@dataclass
class MultiplyResult:
    """
    Dataclass wrapper around a multiplication result
    """
    value: int

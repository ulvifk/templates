from abc import ABC
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TSNode(ABC):
    id: int

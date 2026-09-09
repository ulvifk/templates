from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Resource:
    id: int
    capacity: int

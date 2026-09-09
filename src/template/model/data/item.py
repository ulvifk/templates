from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Item:
    id: int
    weight: int

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Assignment:
    resource_id: int
    item_ids: tuple[int, ...]

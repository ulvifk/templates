from dataclasses import dataclass

from template.model.data.item import Item
from template.model.data.resource import Resource


@dataclass(frozen=True, slots=True)
class ProblemData:
    items: tuple[Item, ...]  # tuple index equals Item.id
    resources: tuple[Resource, ...]  # tuple index equals Resource.id

from abc import ABC, abstractmethod

from template.solvers.branch_price.branch_node import BranchNode
from template.solvers.column_generation.column import Column


class BranchingRule(ABC):
    @abstractmethod
    def get_children(
        self, node: BranchNode, column_values: dict[Column, float]
    ) -> list[BranchNode]:
        """Return the children that split the fractionality; an empty list means the node is integral."""


class MostFractionalResourceRule(BranchingRule):
    """Resource use first, then a single item assignment inside it, always taking the entry closest to half integral."""

    def get_children(
        self, node: BranchNode, column_values: dict[Column, float]
    ) -> list[BranchNode]:
        raise NotImplementedError(
            "Aggregate the column values per resource and per (resource, item), then return the two children fixing the entry closest to half integral."
        )

import math
from dataclasses import dataclass

from template.solvers.branch_and_price_solver.branching.branching_decision import (
    BranchingDecision,
)
from template.solvers.branch_and_price_solver.column_generation.column import Column


@dataclass
class BranchNode:
    """A node's branching decisions and solved relaxation."""

    branching_decisions: tuple[BranchingDecision, ...]

    # the parent's bound until the node is solved, then its own
    lower_bound: float
    # [column] -> value in the node's relaxation; empty until the node is solved
    master_relaxation_solution: dict[Column, float]

    def is_column_compatible(self, column: Column) -> bool:
        return all(
            decision.is_column_compatible(column)
            for decision in self.branching_decisions
        )


class BranchNodeFactory:
    @staticmethod
    def build_root() -> BranchNode:
        return BranchNode(
            branching_decisions=(),
            lower_bound=-math.inf,
            master_relaxation_solution={},
        )

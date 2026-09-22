from dataclasses import dataclass

from template.solvers.branch_and_price_solver.branching.branching_decision import (
    BranchingDecision,
)
from template.solvers.branch_and_price_solver.column_generation.column import Column
from template.solvers.branch_and_price_solver.column_generation.master.master_problem import (
    MasterProblem,
)
from template.solvers.branch_and_price_solver.column_generation.pricing.pricing_problem import (
    PricingProblem,
)


@dataclass
class BranchNode:
    """A node's accumulated branching decisions and its bound."""

    branching_decisions: tuple[BranchingDecision, ...]
    lower_bound: float  # the parent's bound until the node is solved, then its own

    def is_column_compatible(self, column: Column) -> bool:
        return all(
            decision.is_column_compatible(column)
            for decision in self.branching_decisions
        )

    def apply_to_master(self, master: MasterProblem) -> None:
        for decision in self.branching_decisions:
            decision.apply_to_master(master)

    def apply_to_pricing(self, pricing_problem: PricingProblem) -> None:
        for decision in self.branching_decisions:
            decision.apply_to_pricing(pricing_problem)

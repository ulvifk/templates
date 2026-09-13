from abc import ABC, abstractmethod

from template.solvers.branch_and_price_solver.branching.branch_node import BranchNode
from template.solvers.branch_and_price_solver.column_generation.pricing.pricing_problem import (
    PricingProblem,
)


class PricingProblemBuilder(ABC):
    # Build the pricer with node.branching_decisions applied to its feasible region
    # and reduced-cost calculation.
    @abstractmethod
    def build(self, node: BranchNode) -> PricingProblem: ...

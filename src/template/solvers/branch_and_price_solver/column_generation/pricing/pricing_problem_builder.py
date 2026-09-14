from abc import ABC, abstractmethod

from template.solvers.branch_and_price_solver.column_generation.pricing.pricing_problem import (
    PricingProblem,
)


class PricingProblemBuilder(ABC):
    # the pricer with no decision applied; the solver applies the node's decisions to it
    @abstractmethod
    def build(self) -> PricingProblem: ...

from abc import ABC, abstractmethod

from template.model.data.problem_data import ProblemData
from template.solvers.column_generation.column import Column
from template.solvers.column_generation.duals import Duals


class PricingProblem(ABC):
    @abstractmethod
    def price(self, duals: Duals) -> list[Column]:
        """Return columns with negative reduced cost; an empty list means the master has converged."""


class KnapsackPricer(PricingProblem):
    """One binary knapsack per resource: pack the items whose duals pay for the resource."""

    _problem_data: ProblemData

    def __init__(self, problem_data: ProblemData) -> None:
        self._problem_data = problem_data

    def price(self, duals: Duals) -> list[Column]:
        raise NotImplementedError(
            "Solve one knapsack per resource under duals.items; return columns with negative reduced cost."
        )

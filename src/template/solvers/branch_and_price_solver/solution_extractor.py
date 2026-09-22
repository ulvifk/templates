from abc import ABC, abstractmethod

from template.model.solution.solution import Solution
from template.solvers.branch_and_price_solver.column_generation.column import Column


class SolutionExtractor(ABC):
    # builds the solution from the incumbent's column values, preserving its
    # objective; an empty mapping means no incumbent and yields the empty solution
    @abstractmethod
    def extract(self, column_values: dict[Column, float]) -> Solution: ...

from abc import ABC, abstractmethod

from template.model.data.problem_data import ProblemData
from template.model.solve_result import SolveResult


class Solver(ABC):
    ZERO_TOLERANCE = 1e-6

    @abstractmethod
    def solve(self, problem_data: ProblemData) -> SolveResult: ...

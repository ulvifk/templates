from abc import ABC, abstractmethod

from template.model.data.problem_data import ProblemData
from template.model.solution.solution import Solution


class FeasibilityCheck(ABC):
    @abstractmethod
    def check(self, solution: Solution, problem_data: ProblemData) -> None: ...

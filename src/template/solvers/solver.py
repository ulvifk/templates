import logging
from abc import ABC, abstractmethod

from template.model.data.problem_data import ProblemData
from template.model.solve_result import SolveResult

logger = logging.getLogger(__name__)


class Solver(ABC):
    @abstractmethod
    def solve(self, problem_data: ProblemData) -> SolveResult: ...

from typing import ClassVar

from template.feasibility.feasibility_check import FeasibilityCheck
from template.model.data.problem_data import ProblemData
from template.model.solution.solution import Solution


class FeasibilityValidation:
    checks: ClassVar[list[FeasibilityCheck]] = []

    @staticmethod
    def validate(solution: Solution, problem_data: ProblemData) -> None:
        for check in FeasibilityValidation.checks:
            check.check(solution, problem_data)

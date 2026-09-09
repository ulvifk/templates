from dataclasses import dataclass
from typing import Any

from template.model.data.problem_data import ProblemData
from template.model.solution.solution import Solution


@dataclass(frozen=True, slots=True)
class SolveResult:
    problem_data: ProblemData
    solution: Solution | None  # None when the solver found no incumbent

    # solver name, status, runtime, objective, bound, and any solver-specific extras
    meta_data: dict[str, Any]

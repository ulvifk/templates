from dataclasses import dataclass
from typing import Any

from template.model.data.problem_data import ProblemData
from template.model.solution.solution import Solution
from template.model.solve_status import SolveStatus


@dataclass(frozen=True, slots=True)
class SolveResult:
    problem_data: ProblemData
    solution: Solution
    solver_name: str
    status: SolveStatus
    runtime_seconds: float
    best_bound: float
    meta_data: dict[str, Any]  # solver-specific extras only

    @property
    def objective_value(self) -> float:
        return float(len(self.solution.used_resource_ids))

from dataclasses import dataclass

from template.solvers.branch_and_price_solver.column_generation.column import Column


@dataclass(frozen=True, slots=True)
class Incumbent:
    objective: float
    column_values: dict[Column, float]  # [column] -> value

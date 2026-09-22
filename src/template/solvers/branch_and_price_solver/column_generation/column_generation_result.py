from dataclasses import dataclass

from template.solvers.branch_and_price_solver.column_generation.column_generation_status import (
    ColumnGenerationStatus,
)


@dataclass(frozen=True, slots=True)
class ColumnGenerationResult:
    status: ColumnGenerationStatus
    bound: float  # math.inf when infeasible

    round_count: int
    new_column_count: int  # columns this node added to the pool

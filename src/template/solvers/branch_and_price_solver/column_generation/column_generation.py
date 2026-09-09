import math

from template.solvers.branch_and_price_solver.column_generation.column_generation_result import (
    ColumnGenerationResult,
)
from template.solvers.branch_and_price_solver.column_generation.column_generation_status import (
    ColumnGenerationStatus,
)
from template.solvers.branch_and_price_solver.column_generation.column_pool import (
    ColumnPool,
)
from template.solvers.branch_and_price_solver.column_generation.master.master_problem import (
    MasterProblem,
)
from template.solvers.branch_and_price_solver.column_generation.pricing.pricing_problem import (
    PricingProblem,
)


class ColumnGeneration:
    """Solve, price, and add columns until pricing certifies convergence."""

    _pricing_problem: PricingProblem
    _column_pool: ColumnPool

    def __init__(
        self, pricing_problem: PricingProblem, column_pool: ColumnPool
    ) -> None:
        self._pricing_problem = pricing_problem
        self._column_pool = column_pool

    def run(self, master: MasterProblem) -> ColumnGenerationResult:
        round_count = 0
        while True:
            objective = master.solve_relaxation()
            round_count += 1

            columns = self._pricing_problem.price(master.get_duals())
            if not columns:
                break

            fresh_columns = self._column_pool.add(columns)
            if not fresh_columns:
                raise RuntimeError(
                    "Pricing returned only known columns without certifying convergence."
                )

            master.add_columns(fresh_columns)

        if not master.is_feasible():
            return ColumnGenerationResult(
                status=ColumnGenerationStatus.INFEASIBLE,
                bound=math.inf,
                round_count=round_count,
            )

        return ColumnGenerationResult(
            status=ColumnGenerationStatus.CONVERGED,
            bound=objective,
            round_count=round_count,
        )

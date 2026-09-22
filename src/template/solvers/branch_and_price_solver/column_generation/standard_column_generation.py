import math

from template.solvers.branch_and_price_solver.column_generation.column_generation import (
    ColumnGeneration,
)
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
from template.solvers.branch_and_price_solver.timing.node_step import NodeStep
from template.solvers.branch_and_price_solver.timing.step_timer import StepTimer


class StandardColumnGeneration(ColumnGeneration):
    def run(
        self,
        master: MasterProblem,
        pricing_problem: PricingProblem,
        column_pool: ColumnPool,
        step_timer: StepTimer,
    ) -> ColumnGenerationResult:
        round_count = 0
        new_column_count = 0
        while True:
            objective = master.solve_relaxation()
            duals = master.get_duals()
            step_timer.finish_step(NodeStep.MASTER_SOLVE)
            round_count += 1

            columns = pricing_problem.price(duals)
            step_timer.finish_step(NodeStep.PRICING)
            if not columns:
                break

            fresh_columns = column_pool.add(columns)
            if not fresh_columns:
                raise RuntimeError(
                    "Pricing returned only known columns without certifying convergence."
                )

            master.add_columns(fresh_columns)
            new_column_count += len(fresh_columns)

        if not master.is_feasible():
            return ColumnGenerationResult(
                status=ColumnGenerationStatus.INFEASIBLE,
                bound=math.inf,
                round_count=round_count,
                new_column_count=new_column_count,
            )

        return ColumnGenerationResult(
            status=ColumnGenerationStatus.CONVERGED,
            bound=objective,
            round_count=round_count,
            new_column_count=new_column_count,
        )

from time import perf_counter

from template.solvers.branch_and_price_solver.column_generation.column_generation import (
    ColumnGeneration,
)
from template.solvers.branch_and_price_solver.column_generation.column_generation_result import (
    ColumnGenerationResult,
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
from template.solvers.branch_and_price_solver.progress.node_component import (
    NodeComponent,
)
from template.solvers.branch_and_price_solver.progress.node_observations import (
    NodeObservations,
)


class TimedColumnGeneration(ColumnGeneration):
    _inner: ColumnGeneration
    _observations: NodeObservations

    def __init__(self, inner: ColumnGeneration, observations: NodeObservations) -> None:
        self._inner = inner
        self._observations = observations

    def run(
        self,
        master: MasterProblem,
        pricing_problem: PricingProblem,
        column_pool: ColumnPool,
    ) -> ColumnGenerationResult:
        pool_size_before = len(column_pool.get_columns())

        started_at = perf_counter()
        result = self._inner.run(master, pricing_problem, column_pool)
        self._observations.seconds_by_component[NodeComponent.COLUMN_GENERATION] = (
            perf_counter() - started_at
        )

        self._observations.round_count = result.round_count
        self._observations.new_column_count = (
            len(column_pool.get_columns()) - pool_size_before
        )

        return result

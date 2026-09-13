from time import perf_counter

from template.solvers.branch_and_price_solver.branching.branch_node import BranchNode
from template.solvers.branch_and_price_solver.column_generation.column import Column
from template.solvers.branch_and_price_solver.column_generation.master.master_problem import (
    MasterProblem,
)
from template.solvers.branch_and_price_solver.column_generation.master.master_problem_builder import (
    MasterProblemBuilder,
)
from template.solvers.branch_and_price_solver.progress.node_component import (
    NodeComponent,
)
from template.solvers.branch_and_price_solver.progress.node_observations import (
    NodeObservations,
)
from template.solvers.branch_and_price_solver.progress.timed_master_problem import (
    TimedMasterProblem,
)


class TimedMasterProblemBuilder(MasterProblemBuilder):
    _inner: MasterProblemBuilder
    _observations: NodeObservations

    def __init__(
        self, inner: MasterProblemBuilder, observations: NodeObservations
    ) -> None:
        self._inner = inner
        self._observations = observations

    def build(self, node: BranchNode, columns: list[Column]) -> MasterProblem:
        started_at = perf_counter()
        master = self._inner.build(node, columns)
        self._observations.seconds_by_component[NodeComponent.MASTER] = (
            perf_counter() - started_at
        )

        self._observations.compatible_column_count = len(columns)

        return TimedMasterProblem(master, self._observations)

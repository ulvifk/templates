from time import perf_counter
from typing import Any

from template.solvers.branch_and_price_solver.column_generation.column import Column
from template.solvers.branch_and_price_solver.column_generation.master.duals import (
    Duals,
)
from template.solvers.branch_and_price_solver.column_generation.master.master_problem import (
    MasterProblem,
)
from template.solvers.branch_and_price_solver.progress.node_component import (
    NodeComponent,
)
from template.solvers.branch_and_price_solver.progress.node_observations import (
    NodeObservations,
)


class TimedMasterProblem(MasterProblem):
    """Times the integrality check and delegates everything else."""

    _inner: MasterProblem
    _observations: NodeObservations

    def __init__(self, inner: MasterProblem, observations: NodeObservations) -> None:
        self._inner = inner
        self._observations = observations

    def add_columns(self, columns: list[Column]) -> None:
        self._inner.add_columns(columns)

    def solve_relaxation(self) -> float:
        return self._inner.solve_relaxation()

    def get_duals(self) -> Duals:
        return self._inner.get_duals()

    def is_feasible(self) -> bool:
        return self._inner.is_feasible()

    def is_integral(self) -> bool:
        started_at = perf_counter()
        integral = self._inner.is_integral()
        self._observations.seconds_by_component[NodeComponent.INTEGRALITY] = (
            perf_counter() - started_at
        )
        self._observations.integral = integral

        return integral

    def get_master_relaxation_solution(self) -> dict[Column, float]:
        return self._inner.get_master_relaxation_solution()

    def dispose(self) -> None:
        self._inner.dispose()

    # decisions call the project master's capabilities through the wrapper
    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

import math
import time

from template.solvers.column_generation.column_generation_result import (
    ColumnGenerationResult,
)
from template.solvers.column_generation.column_pool import ColumnPool
from template.solvers.column_generation.master_problem import MasterProblem
from template.solvers.column_generation.pricing_problem import PricingProblem


class ColumnGeneration:
    """One master's pricing loop; the pricer sees only the duals, so every restriction has to reach it through the master rows."""

    _pricer: PricingProblem
    _pool: ColumnPool

    def __init__(self, pricer: PricingProblem, pool: ColumnPool) -> None:
        self._pricer = pricer
        self._pool = pool

    def run(
        self, master: MasterProblem, time_left_seconds: float
    ) -> ColumnGenerationResult:
        deadline = time.perf_counter() + time_left_seconds

        master_seconds = 0.0
        pricing_seconds = 0.0
        rounds = 0
        while True:
            started = time.perf_counter()
            objective = master.solve_relaxation()
            master_seconds += time.perf_counter() - started
            rounds += 1

            if time.perf_counter() > deadline:
                return self._get_result(
                    objective, False, rounds, master_seconds, pricing_seconds
                )

            started = time.perf_counter()
            columns = self._pricer.price(master.get_duals())
            pricing_seconds += time.perf_counter() - started

            fresh = self._pool.add(columns)
            if not fresh:
                break
            master.add_columns(fresh)

        return self._get_result(
            self._get_converged_bound(master, objective),
            True,
            rounds,
            master_seconds,
            pricing_seconds,
        )

    def _get_result(
        self,
        bound: float,
        converged: bool,
        rounds: int,
        master_seconds: float,
        pricing_seconds: float,
    ) -> ColumnGenerationResult:
        return ColumnGenerationResult(
            bound=bound,
            converged=converged,
            rounds=rounds,
            column_count=len(self._pool.get_columns()),
            master_seconds=master_seconds,
            pricing_seconds=pricing_seconds,
        )

    @staticmethod
    def _get_converged_bound(master: MasterProblem, objective: float) -> float:
        """Artificials still in use mean the columns cannot cover the rows, so the master is infeasible."""
        if master.get_artificial_usage() > MasterProblem.ARTIFICIAL_TOLERANCE:
            return math.inf
        return objective

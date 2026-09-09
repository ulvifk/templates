import time

import gurobipy

from template.model.data.problem_data import ProblemData
from template.model.solution.solution import Solution
from template.model.solve_result import SolveResult
from template.model.solve_status import SolveStatus
from template.solvers.column_generation.column import build_solution_from_columns
from template.solvers.column_generation.column_generation import ColumnGeneration
from template.solvers.column_generation.column_generation_config import (
    ColumnGenerationConfig,
)
from template.solvers.column_generation.column_generation_result import (
    ColumnGenerationResult,
)
from template.solvers.column_generation.column_pool import ColumnPool
from template.solvers.column_generation.master_problem import SetCoveringMaster
from template.solvers.column_generation.pricing_problem import KnapsackPricer
from template.solvers.solver import Solver


class ColumnGenerationSolver(Solver):
    """Root column generation, then one integer solve over the generated columns as a heuristic incumbent."""

    SOLVER_NAME = "column-generation"

    _config: ColumnGenerationConfig

    def __init__(self, config: ColumnGenerationConfig) -> None:
        self._config = config

    def solve(self, problem_data: ProblemData) -> SolveResult:
        started = time.perf_counter()

        with gurobipy.Env() as env:
            pool = ColumnPool()
            master = SetCoveringMaster(env, problem_data, pool.get_columns())
            column_generation = ColumnGeneration(KnapsackPricer(problem_data), pool)

            result = column_generation.run(master, self._config.time_limit_seconds)

            solution = Solution(assignments=())
            if master.solve_integer(self._config.integer_time_limit_seconds):
                solution = build_solution_from_columns(master.get_column_values())
            master.close()

        return self._build_result(
            problem_data, solution, result, time.perf_counter() - started
        )

    def _build_result(
        self,
        problem_data: ProblemData,
        solution: Solution,
        result: ColumnGenerationResult,
        runtime_seconds: float,
    ) -> SolveResult:
        return SolveResult(
            problem_data=problem_data,
            solution=solution,
            solver_name=self.SOLVER_NAME,
            status=self._get_status(solution, result),
            runtime_seconds=runtime_seconds,
            best_bound=result.bound,
            meta_data={
                "rounds": result.rounds,
                "column_count": result.column_count,
                "master_seconds": result.master_seconds,
                "pricing_seconds": result.pricing_seconds,
            },
        )

    def _get_status(
        self, solution: Solution, result: ColumnGenerationResult
    ) -> SolveStatus:
        """The integer solve is a heuristic, so only a solution matching the root bound proves optimality."""
        if not solution.assignments:
            return SolveStatus.NO_INCUMBENT
        if not result.converged:
            return SolveStatus.TIME_LIMIT
        if len(solution.assignments) <= result.bound + self.ZERO_TOLERANCE:
            return SolveStatus.OPTIMAL
        return SolveStatus.TIME_LIMIT

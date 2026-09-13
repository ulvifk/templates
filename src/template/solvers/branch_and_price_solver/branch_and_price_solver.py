import math
import time
from abc import ABC, abstractmethod
from typing import Any

from template.constants import ZERO_TOLERANCE
from template.model.data.problem_data import ProblemData
from template.model.solution.solution import Solution
from template.model.solve_result import SolveResult
from template.solvers.branch_and_price_solver.branch_and_price_config import (
    BranchAndPriceConfig,
)
from template.solvers.branch_and_price_solver.branching.branch_node import (
    BranchNode,
    BranchNodeFactory,
)
from template.solvers.branch_and_price_solver.column_generation.column import Column
from template.solvers.branch_and_price_solver.column_generation.column_generation_status import (
    ColumnGenerationStatus,
)
from template.solvers.branch_and_price_solver.column_generation.column_pool import (
    ColumnPool,
)
from template.solvers.solver import Solver


class BranchAndPriceSolver(Solver, ABC):
    SOLVER_NAME = "branch-and-price"

    _config: BranchAndPriceConfig

    _problem_data: ProblemData
    _column_pool: ColumnPool

    _best_node: BranchNode | None  # the best integral node found so far
    _root_bound: float
    _explored_node_count: int

    _started_at: float
    _deadline: float

    def __init__(self, config: BranchAndPriceConfig) -> None:
        self._config = config

    def solve(self, problem_data: ProblemData) -> SolveResult:
        self._initialize_search(problem_data)

        while time.perf_counter() < self._deadline:
            node = self._config.node_selector.pop()
            if node is None:
                break
            if self._is_closed_by_incumbent(node.lower_bound):
                continue

            self._explored_node_count += 1
            columns = [
                column
                for column in self._column_pool.get_columns()
                if node.is_column_compatible(column)
            ]
            master = self._config.master_problem_builder.build(node, columns)
            pricing_problem = self._config.pricing_problem_builder.build(node)

            result = self._config.column_generation.run(
                master, pricing_problem, self._column_pool
            )
            pricing_problem.dispose()

            node.lower_bound = result.bound
            if self._explored_node_count == 1:
                self._root_bound = result.bound

            if result.status is ColumnGenerationStatus.INFEASIBLE:
                master.dispose()
                continue

            node.master_relaxation_solution = master.get_master_relaxation_solution()
            integral = master.is_integral()
            master.dispose()

            if self._is_closed_by_incumbent(node.lower_bound):
                continue
            if integral:
                self._best_node = node
                continue

            children = self._config.branching_rule.get_children(node)
            self._config.node_selector.push(children)

        return self._build_result()

    def _initialize_search(self, problem_data: ProblemData) -> None:
        self._problem_data = problem_data

        self._column_pool = ColumnPool()

        self._best_node = None
        self._root_bound = -math.inf
        self._explored_node_count = 0

        self._started_at = time.perf_counter()
        self._deadline = self._started_at + self._config.time_limit_seconds

        self._config.node_selector.push([BranchNodeFactory.build_root()])

    # the objective is minimized, so a bound that reaches the incumbent proves nothing
    # below it is left: a node with such a bound is pruned, a tree with such a bound
    # is solved
    def _is_closed_by_incumbent(self, bound: float) -> bool:
        return bound >= self._get_incumbent_objective() - ZERO_TOLERANCE

    def _get_incumbent_objective(self) -> float:
        if self._best_node is None:
            return math.inf

        return self._best_node.lower_bound

    def _get_incumbent_master_relaxation_solution(self) -> dict[Column, float]:
        if self._best_node is None:
            return {}

        return self._best_node.master_relaxation_solution

    def _build_result(self) -> SolveResult:
        solution = self._extract_solution(
            self._get_incumbent_master_relaxation_solution()
        )

        return SolveResult(
            problem_data=self._problem_data,
            solution=solution,
            meta_data=self._build_meta_data(),
        )

    def _build_meta_data(self) -> dict[str, Any]:
        best_bound = self._get_best_bound()

        return {
            "solver_name": self.SOLVER_NAME,
            "status": self._get_status(best_bound),
            "runtime_seconds": time.perf_counter() - self._started_at,
            "objective": self._get_incumbent_objective(),
            "best_bound": best_bound,
            "root_bound": self._root_bound,
            "explored_node_count": self._explored_node_count,
            "column_count": len(self._column_pool.get_columns()),
        }

    def _get_best_bound(self) -> float:
        open_bound = min(
            self._config.node_selector.get_best_lower_bound(),
            self._get_incumbent_objective(),
        )

        return max(self._root_bound, open_bound)

    def _get_status(self, best_bound: float) -> str:
        if self._best_node is None:
            if self._config.node_selector.get_best_lower_bound() == math.inf:
                return "infeasible"

            return "time-limit"
        if self._is_closed_by_incumbent(best_bound):
            return "optimal"

        return "time-limit"

    # build the solution from the incumbent's master relaxation solution, preserving
    # its objective; an empty relaxation means no incumbent and yields the empty
    # solution
    @abstractmethod
    def _extract_solution(
        self, master_relaxation_solution: dict[Column, float]
    ) -> Solution: ...

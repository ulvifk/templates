import math
from collections.abc import Hashable
from dataclasses import dataclass, replace
from typing import cast

import pytest

from template.model.data.problem_data import ProblemData
from template.model.solution.solution import Solution
from template.solvers.branch_and_price_solver.bounding.relaxation_lower_bound_generator import (
    RelaxationLowerBoundGenerator,
)
from template.solvers.branch_and_price_solver.branch_and_price_config import (
    BranchAndPriceConfig,
)
from template.solvers.branch_and_price_solver.branch_and_price_solver import (
    BranchAndPriceSolver,
)
from template.solvers.branch_and_price_solver.branching.branch_node import (
    BranchNode,
)
from template.solvers.branch_and_price_solver.branching.branching_rule.branching_rule import (
    BranchingRule,
)
from template.solvers.branch_and_price_solver.branching.node_selector.best_first_node_selector import (
    BestFirstNodeSelector,
)
from template.solvers.branch_and_price_solver.column_generation.column import Column
from template.solvers.branch_and_price_solver.column_generation.master.duals import (
    Duals,
)
from template.solvers.branch_and_price_solver.column_generation.master.master_problem import (
    MasterProblem,
)
from template.solvers.branch_and_price_solver.column_generation.master.master_problem_builder import (
    MasterProblemBuilder,
)
from template.solvers.branch_and_price_solver.column_generation.pricing.composite_pricing_problem import (
    CompositePricingProblem,
)
from template.solvers.branch_and_price_solver.column_generation.pricing.pricing_problem import (
    PricingProblem,
)
from template.solvers.branch_and_price_solver.column_generation.pricing.pricing_problem_builder import (
    PricingProblemBuilder,
)
from template.solvers.branch_and_price_solver.column_generation.standard_column_generation import (
    StandardColumnGeneration,
)
from template.solvers.branch_and_price_solver.incumbent.no_incumbent_generator import (
    NoIncumbentGenerator,
)
from template.solvers.branch_and_price_solver.node_evaluation import NodeEvaluation
from template.solvers.branch_and_price_solver.progress.progress_logger import (
    ProgressLogger,
)
from template.solvers.branch_and_price_solver.solution_extractor import (
    SolutionExtractor,
)
from template.solvers.branch_and_price_solver.timing.system_clock import SystemClock


@dataclass(frozen=True, slots=True)
class CategoryColumn(Column):
    category: str
    name: str

    def get_key(self) -> Hashable:
        return self.category, self.name


@dataclass(frozen=True, slots=True)
class CoveringRow:
    lower_bound: float
    upper_bound: float
    category: str

    def get_coefficient(self, column: Column) -> float:
        category_column = cast(CategoryColumn, column)
        return float(category_column.category == self.category)


@dataclass(frozen=True, slots=True)
class CoveringDuals(Duals):
    row_duals: dict[CoveringRow, float]


class CoveringMasterProblem(MasterProblem):
    """Solves disjoint covering rows with positive costs and a feasible seed per row."""

    _columns: list[Column]
    _rows: list[CoveringRow]
    _duals: CoveringDuals
    _relaxation_solution: dict[Column, float]
    _objective: float
    _feasible: bool

    disposed: bool
    solve_objectives: list[float]
    dual_history: list[CoveringDuals]

    def __init__(self, columns: list[Column], rows: list[CoveringRow]) -> None:
        self._columns = columns
        self._rows = rows
        self._duals = CoveringDuals(row_duals={})
        self._relaxation_solution = {}
        self._objective = math.inf
        self._feasible = False

        self.disposed = False
        self.solve_objectives = []
        self.dual_history = []

    @property
    def rows(self) -> list[CoveringRow]:
        return self._rows

    def add_columns(self, columns: list[Column]) -> None:
        self._columns.extend(columns)

    def solve_relaxation(self) -> float:
        self._relaxation_solution = {}
        row_duals: dict[CoveringRow, float] = {}
        self._objective = 0.0
        self._feasible = True

        for row in self._rows:
            candidates = [
                column for column in self._columns if row.get_coefficient(column) > 0.0
            ]
            if not candidates:
                self._objective = math.inf
                self._feasible = False
                row_duals[row] = 0.0
                continue

            best_column = min(
                candidates,
                key=lambda column: column.cost / row.get_coefficient(column),
            )
            coefficient = row.get_coefficient(best_column)
            value = row.lower_bound / coefficient
            row_duals[row] = best_column.cost / coefficient
            self._relaxation_solution[best_column] = value
            self._objective += best_column.cost * value

        self._duals = CoveringDuals(row_duals=row_duals)
        self.solve_objectives.append(self._objective)
        self.dual_history.append(self._duals)

        return self._objective

    def get_duals(self) -> CoveringDuals:
        return self._duals

    def is_feasible(self) -> bool:
        return self._feasible

    def is_integral(self) -> bool:
        if not self._feasible:
            return False

        return all(value.is_integer() for value in self._relaxation_solution.values())

    def get_master_relaxation_solution(self) -> dict[Column, float]:
        return self._relaxation_solution

    def dispose(self) -> None:
        self.disposed = True


class CoveringMasterProblemBuilder(MasterProblemBuilder):
    _initial_columns: list[Column]
    _rows: list[CoveringRow]

    built_masters: list[CoveringMasterProblem]

    def __init__(self, initial_columns: list[Column], rows: list[CoveringRow]) -> None:
        self._initial_columns = initial_columns
        self._rows = rows

        self.built_masters = []

    def build(self, columns: list[Column]) -> CoveringMasterProblem:
        master = CoveringMasterProblem([*self._initial_columns, *columns], self._rows)
        self.built_masters.append(master)

        return master


class CategoryPricingProblem(PricingProblem):
    _candidates: tuple[CategoryColumn, ...]
    _rows: list[CoveringRow]

    dual_history: list[CoveringDuals]
    reduced_cost_history: list[list[float]]
    disposed: bool

    def __init__(
        self, candidates: tuple[CategoryColumn, ...], rows: list[CoveringRow]
    ) -> None:
        self._candidates = candidates
        self._rows = rows

        self.dual_history = []
        self.reduced_cost_history = []
        self.disposed = False

    @property
    def rows(self) -> list[CoveringRow]:
        return self._rows

    def price(self, duals: Duals) -> list[Column]:
        covering_duals = cast(CoveringDuals, duals)
        self.dual_history.append(covering_duals)
        reduced_costs: list[float] = []
        improving_columns: list[Column] = []

        for candidate in self._candidates:
            reduced_cost = candidate.cost
            for row in self._rows:
                reduced_cost -= covering_duals.row_duals[row] * row.get_coefficient(
                    candidate
                )
            reduced_costs.append(reduced_cost)
            if reduced_cost < 0.0:
                improving_columns.append(candidate)

        self.reduced_cost_history.append(reduced_costs)

        return improving_columns

    def dispose(self) -> None:
        self.disposed = True


class CoveringPricingProblemBuilder(PricingProblemBuilder):
    _candidate_pools: tuple[tuple[CategoryColumn, ...], ...]
    _rows: list[CoveringRow]

    built_pricing_problems: list[CompositePricingProblem[CategoryPricingProblem]]

    def __init__(
        self,
        candidate_pools: tuple[tuple[CategoryColumn, ...], ...],
        rows: list[CoveringRow],
    ) -> None:
        self._candidate_pools = candidate_pools
        self._rows = rows

        self.built_pricing_problems = []

    def build(self) -> CompositePricingProblem[CategoryPricingProblem]:
        components = [
            CategoryPricingProblem(candidate_pool, self._rows)
            for candidate_pool in self._candidate_pools
        ]
        pricing_problem = CompositePricingProblem(components)
        self.built_pricing_problems.append(pricing_problem)

        return pricing_problem


class NoBranchingRule(BranchingRule):
    def get_children(
        self, node: BranchNode, evaluation: NodeEvaluation
    ) -> list[BranchNode]:
        return []


class EmptySolutionExtractor(SolutionExtractor):
    def extract(self, column_values: dict[Column, float]) -> Solution:
        return Solution()


def build_covering_config(
    master_builder: CoveringMasterProblemBuilder,
    pricing_builder: CoveringPricingProblemBuilder,
) -> BranchAndPriceConfig:
    return BranchAndPriceConfig(
        time_limit_seconds=1000.0,
        clock=SystemClock(),
        node_selector=BestFirstNodeSelector(),
        branching_rule=NoBranchingRule(),
        master_problem_builder=master_builder,
        pricing_problem_builder=pricing_builder,
        column_generation=StandardColumnGeneration(),
        node_lower_bound_generator=RelaxationLowerBoundGenerator(),
        node_incumbent_generator=NoIncumbentGenerator(),
        solution_extractor=EmptySolutionExtractor(),
        observers=[],
    )


def build_rows() -> tuple[CoveringRow, CoveringRow]:
    return (
        CoveringRow(lower_bound=1.0, upper_bound=math.inf, category="red"),
        CoveringRow(lower_bound=1.0, upper_bound=math.inf, category="blue"),
    )


@pytest.mark.parametrize("logging_enabled", [False, True])
def test_covering_rows_drive_initial_and_priced_columns_to_convergence(
    logging_enabled: bool,
) -> None:
    red_row, blue_row = build_rows()
    red_seed = CategoryColumn(cost=10.0, category="red", name="seed")
    blue_seed = CategoryColumn(cost=10.0, category="blue", name="seed")
    red_cheap = CategoryColumn(cost=2.0, category="red", name="cheap")
    blue_cheap = CategoryColumn(cost=3.0, category="blue", name="cheap")
    rows = [red_row, blue_row]
    master_builder = CoveringMasterProblemBuilder([red_seed, blue_seed], rows)
    pricing_builder = CoveringPricingProblemBuilder(((red_cheap,), (blue_cheap,)), rows)
    config = build_covering_config(master_builder, pricing_builder)
    if logging_enabled:
        config = replace(config, observers=[ProgressLogger()])

    result = BranchAndPriceSolver(config).solve(ProblemData())

    assert result.meta_data["status"] == "optimal"
    assert result.meta_data["objective"] == pytest.approx(5.0)
    assert result.meta_data["column_count"] == 2
    assert result.meta_data["explored_node_count"] == 1

    master = master_builder.built_masters[0]
    assert master.rows == [red_row, blue_row]
    assert master.solve_objectives == [20.0, 5.0]
    assert [duals.row_duals for duals in master.dual_history] == [
        {red_row: 10.0, blue_row: 10.0},
        {red_row: 2.0, blue_row: 3.0},
    ]
    assert master.get_master_relaxation_solution() == {
        red_cheap: 1.0,
        blue_cheap: 1.0,
    }
    assert red_row.get_coefficient(red_seed) == 1.0
    assert red_row.get_coefficient(red_cheap) == 1.0
    assert blue_row.get_coefficient(red_seed) == 0.0
    assert blue_row.get_coefficient(blue_cheap) == 1.0
    assert master.disposed

    composite_pricing_problem = pricing_builder.built_pricing_problems[0]
    red_pricer, blue_pricer = composite_pricing_problem.get_pricing_problems()
    assert red_pricer.rows == [red_row, blue_row]
    assert blue_pricer.rows == [red_row, blue_row]
    assert [dual.row_duals for dual in red_pricer.dual_history] == [
        {red_row: 10.0, blue_row: 10.0},
        {red_row: 2.0, blue_row: 3.0},
    ]
    assert [dual.row_duals for dual in blue_pricer.dual_history] == [
        {red_row: 10.0, blue_row: 10.0},
        {red_row: 2.0, blue_row: 3.0},
    ]
    assert red_pricer.reduced_cost_history == [[-8.0], [0.0]]
    assert blue_pricer.reduced_cost_history == [[-7.0], [0.0]]
    assert red_pricer.disposed
    assert blue_pricer.disposed

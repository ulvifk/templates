import math
import time
from collections.abc import Hashable
from dataclasses import dataclass
from typing import Any
from unittest.mock import Mock, call

import pytest

from template.model.data.problem_data import ProblemData
from template.model.solution.solution import Solution
from template.solvers.branch_and_price_solver.bounding.node_lower_bound_generator import (
    NodeLowerBoundGenerator,
)
from template.solvers.branch_and_price_solver.branch_and_price_config import (
    BranchAndPriceConfig,
)
from template.solvers.branch_and_price_solver.branch_and_price_solver import (
    BranchAndPriceSolver,
)
from template.solvers.branch_and_price_solver.branching.branch_node import (
    BranchNode,
    BranchNodeFactory,
)
from template.solvers.branch_and_price_solver.branching.branching_decision import (
    BranchingDecision,
)
from template.solvers.branch_and_price_solver.branching.branching_rule.branching_rule import (
    BranchingRule,
)
from template.solvers.branch_and_price_solver.branching.node_selector.best_first_node_selector import (
    BestFirstNodeSelector,
)
from template.solvers.branch_and_price_solver.column_generation.column import Column
from template.solvers.branch_and_price_solver.column_generation.column_generation_result import (
    ColumnGenerationResult,
)
from template.solvers.branch_and_price_solver.column_generation.master.duals import (
    Duals,
)
from template.solvers.branch_and_price_solver.column_generation.master.master_problem import (
    MasterProblem,
)
from template.solvers.branch_and_price_solver.column_generation.master.master_problem_builder import (
    MasterProblemBuilder,
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
from template.solvers.branch_and_price_solver.incumbent.incumbent import Incumbent
from template.solvers.branch_and_price_solver.incumbent.node_incumbent_generator import (
    NodeIncumbentGenerator,
)

ROOT_OBJECTIVE = 10.0
CHILD_OBJECTIVES = (12.0, 11.0)
HEURISTIC_OBJECTIVE = 10.5

ROOT_NODE = BranchNode(
    branching_decisions=(),
    lower_bound=-math.inf,
    master_relaxation_solution={},
)


@dataclass(frozen=True, slots=True)
class FakeColumn(Column):
    key: tuple[int, ...]

    def get_key(self) -> Hashable:
        return self.key


HEURISTIC_COLUMN_VALUES: dict[Column, float] = {
    FakeColumn(cost=HEURISTIC_OBJECTIVE, key=(9,)): 1.0
}


class FakeMasterProblem(MasterProblem):
    """Reports the objective the scripted tree assigned to its node."""

    _objective: float
    _feasible: bool
    _integral: bool

    def __init__(
        self, objective: float, feasible: bool = True, integral: bool = False
    ) -> None:
        self._objective = objective
        self._feasible = feasible
        self._integral = integral

    def add_columns(self, columns: list[Column]) -> None:
        return None

    def solve_relaxation(self) -> float:
        return self._objective

    def get_duals(self) -> Duals:
        return Duals()

    def is_feasible(self) -> bool:
        return self._feasible

    def is_integral(self) -> bool:
        return self._integral

    def get_master_relaxation_solution(self) -> dict[Column, float]:
        if not self._feasible:
            raise AssertionError(
                "infeasible nodes must not expose master relaxation solution"
            )

        return {FakeColumn(cost=self._objective, key=(1,)): 1.0}

    def dispose(self) -> None:
        return None


class FakeMasterProblemBuilder(MasterProblemBuilder):
    # [id of node] -> the objective its master reports
    _objectives: dict[int, float]
    _integral_node_ids: set[int]
    _feasible: bool

    def __init__(
        self,
        objectives: dict[int, float],
        integral_node_ids: set[int],
        feasible: bool = True,
    ) -> None:
        self._objectives = objectives
        self._integral_node_ids = integral_node_ids
        self._feasible = feasible

    def build(self, node: BranchNode, columns: list[Column]) -> MasterProblem:
        return FakeMasterProblem(
            self._objectives[id(node)],
            self._feasible,
            id(node) in self._integral_node_ids,
        )


class NullPricingProblem(PricingProblem):
    def price(self, duals: Duals) -> list[Column]:
        return []

    def dispose(self) -> None:
        return None


class NullPricingProblemBuilder(PricingProblemBuilder):
    def build(self, node: BranchNode) -> PricingProblem:
        return NullPricingProblem()


class FakeBranchAndPriceSolver(BranchAndPriceSolver):
    def _extract_solution(self, column_values: dict[Column, float]) -> Solution:
        return Solution()


class FakeBranchingRule(BranchingRule):
    """Splits the root into two integral children and stops there."""

    # [id of node] -> the objective its master reports
    _objectives: dict[int, float]
    _integral_node_ids: set[int]

    def __init__(
        self, objectives: dict[int, float], integral_node_ids: set[int]
    ) -> None:
        self._objectives = objectives
        self._integral_node_ids = integral_node_ids

    def get_children(self, node: BranchNode) -> list[BranchNode]:
        children: list[BranchNode] = []
        for objective in CHILD_OBJECTIVES:
            child = BranchNode(
                branching_decisions=node.branching_decisions,
                lower_bound=node.lower_bound,
                master_relaxation_solution={},
            )
            self._objectives[id(child)] = objective
            self._integral_node_ids.add(id(child))
            children.append(child)

        return children


class RelaxationLowerBoundGenerator(NodeLowerBoundGenerator):
    """Reports the relaxation bound unchanged."""

    def generate(
        self, node: BranchNode, master: MasterProblem, result: ColumnGenerationResult
    ) -> float:
        return result.bound


class IncrementedLowerBoundGenerator(NodeLowerBoundGenerator):
    """Reports a bound one unit above the relaxation."""

    def generate(
        self, node: BranchNode, master: MasterProblem, result: ColumnGenerationResult
    ) -> float:
        return result.bound + 1.0


class NullIncumbentGenerator(NodeIncumbentGenerator):
    """Finds nothing on any node."""

    def generate(self, node: BranchNode, master: MasterProblem) -> Incumbent | None:
        return None


class ScriptedIncumbentGenerator(NodeIncumbentGenerator):
    """Finds the same scripted incumbent on every fractional node."""

    def generate(self, node: BranchNode, master: MasterProblem) -> Incumbent | None:
        return Incumbent(HEURISTIC_OBJECTIVE, HEURISTIC_COLUMN_VALUES)


RELAXATION_LOWER_BOUND_GENERATOR = RelaxationLowerBoundGenerator()
NULL_INCUMBENT_GENERATOR = NullIncumbentGenerator()


def build_root() -> BranchNode:
    return ROOT_NODE


def solve_scripted_tree(
    monkeypatch: pytest.MonkeyPatch,
    time_limit_seconds: float = 1000.0,
    feasible: bool = True,
    root_is_integral: bool = False,
    node_lower_bound_generator: NodeLowerBoundGenerator = RELAXATION_LOWER_BOUND_GENERATOR,
    node_incumbent_generator: NodeIncumbentGenerator = NULL_INCUMBENT_GENERATOR,
) -> dict[str, Any]:
    monkeypatch.setattr(BranchNodeFactory, "build_root", build_root)

    ROOT_NODE.lower_bound = -math.inf
    ROOT_NODE.branching_decisions = ()
    ROOT_NODE.master_relaxation_solution = {}

    objectives = {id(ROOT_NODE): ROOT_OBJECTIVE}
    integral_node_ids = {id(ROOT_NODE)} if root_is_integral else set()
    solver = FakeBranchAndPriceSolver(
        BranchAndPriceConfig(
            time_limit_seconds=time_limit_seconds,
            node_selector=BestFirstNodeSelector(),
            branching_rule=FakeBranchingRule(objectives, integral_node_ids),
            master_problem_builder=FakeMasterProblemBuilder(
                objectives, integral_node_ids, feasible
            ),
            pricing_problem_builder=NullPricingProblemBuilder(),
            column_generation=StandardColumnGeneration(),
            node_lower_bound_generator=node_lower_bound_generator,
            node_incumbent_generator=node_incumbent_generator,
        )
    )

    return solver.solve(ProblemData()).meta_data


def test_the_search_keeps_the_best_of_the_integral_children(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    meta_data = solve_scripted_tree(monkeypatch)

    assert meta_data["objective"] == 11.0


def test_the_search_explores_the_root_and_both_children(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    meta_data = solve_scripted_tree(monkeypatch)

    assert meta_data["explored_node_count"] == 3


def test_an_exhausted_tree_is_reported_as_optimal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    meta_data = solve_scripted_tree(monkeypatch)

    assert meta_data["status"] == "optimal"
    assert meta_data["best_bound"] == 11.0


def test_negative_objectives_are_not_clamped_to_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(globals(), "ROOT_OBJECTIVE", -10.0)
    monkeypatch.setitem(globals(), "CHILD_OBJECTIVES", (-9.0, -8.0))

    meta_data = solve_scripted_tree(monkeypatch)

    assert meta_data["objective"] == -9.0
    assert meta_data["root_bound"] == -10.0
    assert meta_data["best_bound"] == -9.0


def test_an_infeasible_root_is_reported_as_infeasible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    meta_data = solve_scripted_tree(monkeypatch, feasible=False)

    assert meta_data["status"] == "infeasible"
    assert meta_data["objective"] == math.inf
    assert meta_data["root_bound"] == math.inf


def test_a_timeout_without_an_incumbent_is_time_limited(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    meta_data = solve_scripted_tree(monkeypatch, time_limit_seconds=0.0)

    assert meta_data["status"] == "time-limit"
    assert meta_data["objective"] == math.inf
    assert meta_data["best_bound"] == -math.inf
    assert meta_data["root_bound"] == -math.inf
    assert meta_data["explored_node_count"] == 0


def test_a_timeout_with_an_incumbent_keeps_time_limit_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = iter((0.0, 1.0, 2.0, 101.0, 102.0))
    monkeypatch.setattr(time, "perf_counter", lambda: next(clock))

    meta_data = solve_scripted_tree(monkeypatch, time_limit_seconds=100.0)

    assert meta_data["status"] == "time-limit"
    assert meta_data["objective"] == 12.0
    assert meta_data["best_bound"] == 10.0
    assert meta_data["explored_node_count"] == 2


def test_a_dominated_inherited_bound_is_pruned_before_solving(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(globals(), "CHILD_OBJECTIVES", (10.0, 12.0))

    meta_data = solve_scripted_tree(monkeypatch)

    assert meta_data["objective"] == 10.0
    assert meta_data["explored_node_count"] == 2


def test_integral_aggregates_preserve_fractional_columns_for_extraction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    master_relaxation_solution = {
        FakeColumn(cost=10.0, key=(1,)): 0.5,
        FakeColumn(cost=10.0, key=(2,)): 0.5,
    }
    extract_solution = Mock(return_value=Solution())
    monkeypatch.setattr(
        FakeMasterProblem,
        "get_master_relaxation_solution",
        lambda self: master_relaxation_solution,
    )
    monkeypatch.setattr(FakeBranchAndPriceSolver, "_extract_solution", extract_solution)

    meta_data = solve_scripted_tree(monkeypatch, root_is_integral=True)

    extract_solution.assert_called_once_with(master_relaxation_solution)
    assert meta_data["objective"] == 10.0


def test_node_decisions_reach_both_builders_and_dispose_each_pricer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    columns: list[Column] = [
        FakeColumn(cost=1.0, key=(1,)),
        FakeColumn(cost=2.0, key=(2,)),
        FakeColumn(cost=3.0, key=(3,)),
    ]
    left_decision = Mock(spec=BranchingDecision)
    left_decision.is_column_compatible.side_effect = lambda column: (
        column.get_key() != (2,)
    )
    second_left_decision = Mock(spec=BranchingDecision)
    second_left_decision.is_column_compatible.side_effect = lambda column: (
        column.get_key() != (3,)
    )
    right_decision = Mock(spec=BranchingDecision)
    right_decision.is_column_compatible.side_effect = lambda column: (
        column.get_key() != (1,)
    )

    left = BranchNode(
        branching_decisions=(left_decision, second_left_decision),
        lower_bound=-math.inf,
        master_relaxation_solution={},
    )
    right = BranchNode(
        branching_decisions=(right_decision,),
        lower_bound=-math.inf,
        master_relaxation_solution={},
    )
    branching_rule = Mock(spec=BranchingRule)
    branching_rule.get_children.return_value = [left, right]

    master_problem_builder = Mock(spec=MasterProblemBuilder)
    master_problem_builder.build.side_effect = [
        FakeMasterProblem(10.0),
        FakeMasterProblem(12.0, integral=True),
        FakeMasterProblem(11.0, feasible=False),
    ]
    pricers = [Mock(spec=PricingProblem) for _ in range(3)]
    pricers[0].price.side_effect = [columns, []]
    pricers[1].price.return_value = []
    pricers[2].price.return_value = []
    pricing_problem_builder = Mock(spec=PricingProblemBuilder)
    pricing_problem_builder.build.side_effect = pricers

    solver = FakeBranchAndPriceSolver(
        BranchAndPriceConfig(
            time_limit_seconds=1000.0,
            node_selector=BestFirstNodeSelector(),
            branching_rule=branching_rule,
            master_problem_builder=master_problem_builder,
            pricing_problem_builder=pricing_problem_builder,
            column_generation=StandardColumnGeneration(),
            node_lower_bound_generator=RELAXATION_LOWER_BOUND_GENERATOR,
            node_incumbent_generator=NULL_INCUMBENT_GENERATOR,
        )
    )
    monkeypatch.setattr(BranchNodeFactory, "build_root", build_root)

    solver.solve(ProblemData())

    assert master_problem_builder.build.call_args_list == [
        call(ROOT_NODE, []),
        call(left, [columns[0]]),
        call(right, columns[1:]),
    ]
    assert pricing_problem_builder.build.call_args_list == [
        call(ROOT_NODE),
        call(left),
        call(right),
    ]
    assert len({id(pricing) for pricing in pricers}) == 3
    for pricing in pricers:
        pricing.dispose.assert_called_once_with()


def test_the_node_lower_bound_generator_sets_the_node_bound(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    meta_data = solve_scripted_tree(
        monkeypatch, node_lower_bound_generator=IncrementedLowerBoundGenerator()
    )

    assert meta_data["root_bound"] == ROOT_OBJECTIVE + 1.0
    assert meta_data["objective"] == min(CHILD_OBJECTIVES) + 1.0


def test_a_heuristic_incumbent_closes_the_tree_and_is_extracted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    extract_solution = Mock(return_value=Solution())
    monkeypatch.setattr(FakeBranchAndPriceSolver, "_extract_solution", extract_solution)

    meta_data = solve_scripted_tree(
        monkeypatch, node_incumbent_generator=ScriptedIncumbentGenerator()
    )

    assert meta_data["status"] == "optimal"
    assert meta_data["objective"] == HEURISTIC_OBJECTIVE
    extract_solution.assert_called_once_with(HEURISTIC_COLUMN_VALUES)

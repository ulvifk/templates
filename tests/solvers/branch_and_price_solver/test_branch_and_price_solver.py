import math
from collections.abc import Hashable, Iterator
from dataclasses import dataclass, replace
from typing import Any
from unittest.mock import ANY, Mock, call

import pytest

from template.model.data.problem_data import ProblemData
from template.model.solution.solution import Solution
from template.solvers.branch_and_price_solver.bounding.node_lower_bound_generator import (
    NodeLowerBoundGenerator,
)
from template.solvers.branch_and_price_solver.branch_and_price_config import (
    BranchAndPriceConfig,
)
from template.solvers.branch_and_price_solver.branch_and_price_observer import (
    BranchAndPriceObserver,
)
from template.solvers.branch_and_price_solver.branch_and_price_solver import (
    BranchAndPriceSolver,
)
from template.solvers.branch_and_price_solver.branching.branch_node import BranchNode
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
from template.solvers.branch_and_price_solver.column_generation.column_generation import (
    ColumnGeneration,
)
from template.solvers.branch_and_price_solver.column_generation.column_generation_result import (
    ColumnGenerationResult,
)
from template.solvers.branch_and_price_solver.column_generation.column_generation_status import (
    ColumnGenerationStatus,
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
from template.solvers.branch_and_price_solver.explored_node import ExploredNode
from template.solvers.branch_and_price_solver.incumbent.incumbent import Incumbent
from template.solvers.branch_and_price_solver.incumbent.node_incumbent_generator import (
    NodeIncumbentGenerator,
)
from template.solvers.branch_and_price_solver.node_context import NodeContext
from template.solvers.branch_and_price_solver.node_evaluation import NodeEvaluation
from template.solvers.branch_and_price_solver.node_outcome import NodeOutcome
from template.solvers.branch_and_price_solver.timing.clock import Clock

ROOT_OBJECTIVE = 10.0
CHILD_OBJECTIVES = (12.0, 11.0)
HEURISTIC_OBJECTIVE = 10.5


@dataclass(frozen=True, slots=True)
class FakeColumn(Column):
    key: tuple[int, ...]

    def get_key(self) -> Hashable:
        return self.key


HEURISTIC_COLUMN_VALUES: dict[Column, float] = {
    FakeColumn(cost=HEURISTIC_OBJECTIVE, key=(9,)): 1.0
}


class FakeClock(Clock):
    """Stands still until a test moves it forward."""

    now: float

    def __init__(self) -> None:
        self.now = 0.0

    def now_seconds(self) -> float:
        return self.now


class NodeDurationObserver(BranchAndPriceObserver):
    """Makes every explored node take the same time on a fake clock."""

    _clock: FakeClock
    _node_seconds: float

    def __init__(self, clock: FakeClock, node_seconds: float) -> None:
        self._clock = clock
        self._node_seconds = node_seconds

    def on_node_explored(self, explored: ExploredNode) -> None:
        self._clock.now += self._node_seconds


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
    """Hands out the scripted masters in exploration order."""

    _masters: Iterator[MasterProblem]

    def __init__(self, masters: list[MasterProblem]) -> None:
        self._masters = iter(masters)

    def build(self, columns: list[Column]) -> MasterProblem:
        return next(self._masters)


class NullPricingProblem(PricingProblem):
    def price(self, duals: Duals) -> list[Column]:
        return []

    def dispose(self) -> None:
        return None


class NullPricingProblemBuilder(PricingProblemBuilder):
    def build(self) -> PricingProblem:
        return NullPricingProblem()


class FakeBranchAndPriceSolver(BranchAndPriceSolver):
    def _extract_solution(self, column_values: dict[Column, float]) -> Solution:
        return Solution()


class FakeBranchingRule(BranchingRule):
    """Splits a node into one child per scripted child objective."""

    def get_children(
        self, node: BranchNode, evaluation: NodeEvaluation
    ) -> list[BranchNode]:
        return [
            BranchNode(
                branching_decisions=node.branching_decisions,
                lower_bound=node.lower_bound,
            )
            for _ in CHILD_OBJECTIVES
        ]


class RelaxationLowerBoundGenerator(NodeLowerBoundGenerator):
    """Reports the relaxation bound unchanged."""

    def generate(self, context: NodeContext) -> float:
        return context.column_generation_result.relaxation_objective


class IncrementedLowerBoundGenerator(NodeLowerBoundGenerator):
    """Reports a bound one unit above the relaxation."""

    def generate(self, context: NodeContext) -> float:
        return context.column_generation_result.relaxation_objective + 1.0


class NullIncumbentGenerator(NodeIncumbentGenerator):
    """Finds nothing on any node."""

    def generate(self, context: NodeContext) -> Incumbent | None:
        return None


class ScriptedIncumbentGenerator(NodeIncumbentGenerator):
    """Finds the same scripted incumbent on every fractional node."""

    def generate(self, context: NodeContext) -> Incumbent | None:
        return Incumbent(HEURISTIC_OBJECTIVE, HEURISTIC_COLUMN_VALUES)


RELAXATION_LOWER_BOUND_GENERATOR = RelaxationLowerBoundGenerator()
NULL_INCUMBENT_GENERATOR = NullIncumbentGenerator()


def build_scripted_config(
    time_limit_seconds: float = 1000.0,
    feasible: bool = True,
    root_is_integral: bool = False,
    node_lower_bound_generator: NodeLowerBoundGenerator = RELAXATION_LOWER_BOUND_GENERATOR,
    node_incumbent_generator: NodeIncumbentGenerator = NULL_INCUMBENT_GENERATOR,
) -> BranchAndPriceConfig:
    root_master = FakeMasterProblem(ROOT_OBJECTIVE, feasible, root_is_integral)
    child_masters = [
        FakeMasterProblem(objective, feasible, integral=True)
        for objective in CHILD_OBJECTIVES
    ]

    return BranchAndPriceConfig(
        time_limit_seconds=time_limit_seconds,
        clock=FakeClock(),
        node_selector=BestFirstNodeSelector(),
        branching_rule=FakeBranchingRule(),
        master_problem_builder=FakeMasterProblemBuilder([root_master, *child_masters]),
        pricing_problem_builder=NullPricingProblemBuilder(),
        column_generation=StandardColumnGeneration(),
        node_lower_bound_generator=node_lower_bound_generator,
        node_incumbent_generator=node_incumbent_generator,
        observers=[],
    )


def solve_scripted_tree(
    time_limit_seconds: float = 1000.0,
    feasible: bool = True,
    root_is_integral: bool = False,
    node_lower_bound_generator: NodeLowerBoundGenerator = RELAXATION_LOWER_BOUND_GENERATOR,
    node_incumbent_generator: NodeIncumbentGenerator = NULL_INCUMBENT_GENERATOR,
) -> dict[str, Any]:
    config = build_scripted_config(
        time_limit_seconds,
        feasible,
        root_is_integral,
        node_lower_bound_generator,
        node_incumbent_generator,
    )

    return FakeBranchAndPriceSolver(config).solve(ProblemData()).meta_data


def test_the_search_keeps_the_best_of_the_integral_children() -> None:
    meta_data = solve_scripted_tree()

    assert meta_data["objective"] == 11.0


def test_the_search_explores_the_root_and_both_children() -> None:
    meta_data = solve_scripted_tree()

    assert meta_data["explored_node_count"] == 3


def test_an_exhausted_tree_is_reported_as_optimal() -> None:
    meta_data = solve_scripted_tree()

    assert meta_data["status"] == "optimal"
    assert meta_data["best_bound"] == 11.0


def test_negative_objectives_are_not_clamped_to_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(globals(), "ROOT_OBJECTIVE", -10.0)
    monkeypatch.setitem(globals(), "CHILD_OBJECTIVES", (-9.0, -8.0))

    meta_data = solve_scripted_tree()

    assert meta_data["objective"] == -9.0
    assert meta_data["root_bound"] == -10.0
    assert meta_data["best_bound"] == -9.0


def test_an_infeasible_root_is_reported_as_infeasible() -> None:
    meta_data = solve_scripted_tree(feasible=False)

    assert meta_data["status"] == "infeasible"
    assert meta_data["objective"] == math.inf
    assert meta_data["root_bound"] == math.inf


def test_a_timeout_without_an_incumbent_is_time_limited() -> None:
    meta_data = solve_scripted_tree(time_limit_seconds=0.0)

    assert meta_data["status"] == "time-limit"
    assert meta_data["objective"] == math.inf
    assert meta_data["best_bound"] == -math.inf
    assert meta_data["root_bound"] == -math.inf
    assert meta_data["explored_node_count"] == 0


def test_a_timeout_with_an_incumbent_keeps_time_limit_status() -> None:
    clock = FakeClock()
    config = replace(
        build_scripted_config(time_limit_seconds=100.0),
        clock=clock,
        observers=[NodeDurationObserver(clock, node_seconds=60.0)],
    )

    meta_data = FakeBranchAndPriceSolver(config).solve(ProblemData()).meta_data

    assert meta_data["status"] == "time-limit"
    assert meta_data["objective"] == 12.0
    assert meta_data["best_bound"] == 10.0
    assert meta_data["explored_node_count"] == 2


def test_a_dominated_inherited_bound_is_pruned_before_solving(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(globals(), "CHILD_OBJECTIVES", (10.0, 12.0))

    meta_data = solve_scripted_tree()

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

    meta_data = solve_scripted_tree(root_is_integral=True)

    extract_solution.assert_called_once_with(master_relaxation_solution)
    assert meta_data["objective"] == 10.0


def test_node_decisions_reach_both_models_and_dispose_each_pricer() -> None:
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
    )
    right = BranchNode(
        branching_decisions=(right_decision,),
        lower_bound=-math.inf,
    )
    branching_rule = Mock(spec=BranchingRule)
    branching_rule.get_children.return_value = [left, right]

    masters = [
        FakeMasterProblem(10.0),
        FakeMasterProblem(12.0, integral=True),
        FakeMasterProblem(11.0, feasible=False),
    ]
    master_problem_builder = Mock(spec=MasterProblemBuilder)
    master_problem_builder.build.side_effect = masters
    pricers = [Mock(spec=PricingProblem) for _ in range(3)]
    pricers[0].price.side_effect = [columns, []]
    pricers[1].price.return_value = []
    pricers[2].price.return_value = []
    pricing_problem_builder = Mock(spec=PricingProblemBuilder)
    pricing_problem_builder.build.side_effect = pricers

    solver = FakeBranchAndPriceSolver(
        BranchAndPriceConfig(
            time_limit_seconds=1000.0,
            clock=FakeClock(),
            node_selector=BestFirstNodeSelector(),
            branching_rule=branching_rule,
            master_problem_builder=master_problem_builder,
            pricing_problem_builder=pricing_problem_builder,
            column_generation=StandardColumnGeneration(),
            node_lower_bound_generator=RELAXATION_LOWER_BOUND_GENERATOR,
            node_incumbent_generator=NULL_INCUMBENT_GENERATOR,
            observers=[],
        )
    )

    solver.solve(ProblemData())

    assert master_problem_builder.build.call_args_list == [
        call([]),
        call([columns[0]]),
        call(columns[1:]),
    ]
    assert pricing_problem_builder.build.call_args_list == [call(), call(), call()]
    assert len({id(pricing) for pricing in pricers}) == 3
    for pricing in pricers:
        pricing.dispose.assert_called_once_with()
    left_decision.apply_to_master.assert_called_once_with(masters[1])
    left_decision.apply_to_pricing.assert_called_once_with(pricers[1])
    second_left_decision.apply_to_master.assert_called_once_with(masters[1])
    second_left_decision.apply_to_pricing.assert_called_once_with(pricers[1])
    right_decision.apply_to_master.assert_called_once_with(masters[2])
    right_decision.apply_to_pricing.assert_called_once_with(pricers[2])


def test_decisions_are_applied_to_both_models_before_column_generation() -> None:
    root_master = FakeMasterProblem(10.0)
    child_master = Mock(spec=MasterProblem)
    master_problem_builder = Mock(spec=MasterProblemBuilder)
    master_problem_builder.build.side_effect = [root_master, child_master]
    root_pricer = Mock(spec=PricingProblem)
    child_pricer = Mock(spec=PricingProblem)
    pricing_problem_builder = Mock(spec=PricingProblemBuilder)
    pricing_problem_builder.build.side_effect = [root_pricer, child_pricer]
    column_generation = Mock(spec=ColumnGeneration)
    column_generation.run.side_effect = [
        ColumnGenerationResult(
            status=ColumnGenerationStatus.CONVERGED,
            relaxation_objective=10.0,
            round_count=1,
            new_column_count=0,
        ),
        ColumnGenerationResult(
            status=ColumnGenerationStatus.INFEASIBLE,
            relaxation_objective=math.inf,
            round_count=1,
            new_column_count=0,
        ),
    ]
    first = Mock(spec=BranchingDecision)
    second = Mock(spec=BranchingDecision)
    manager = Mock()
    manager.attach_mock(first, "first")
    manager.attach_mock(second, "second")
    manager.attach_mock(column_generation, "column_generation")
    child = BranchNode(branching_decisions=(first, second), lower_bound=10.0)
    branching_rule = Mock(spec=BranchingRule)
    branching_rule.get_children.return_value = [child]
    solver = FakeBranchAndPriceSolver(
        BranchAndPriceConfig(
            time_limit_seconds=1000.0,
            clock=FakeClock(),
            node_selector=BestFirstNodeSelector(),
            branching_rule=branching_rule,
            master_problem_builder=master_problem_builder,
            pricing_problem_builder=pricing_problem_builder,
            column_generation=column_generation,
            node_lower_bound_generator=RELAXATION_LOWER_BOUND_GENERATOR,
            node_incumbent_generator=NULL_INCUMBENT_GENERATOR,
            observers=[],
        )
    )

    solver.solve(ProblemData())

    assert manager.mock_calls == [
        call.column_generation.run(root_master, root_pricer, ANY, ANY),
        call.first.apply_to_master(child_master),
        call.second.apply_to_master(child_master),
        call.first.apply_to_pricing(child_pricer),
        call.second.apply_to_pricing(child_pricer),
        call.column_generation.run(child_master, child_pricer, ANY, ANY),
    ]


def test_the_branching_rule_reads_the_relaxation_from_the_evaluation() -> None:
    branching_rule = Mock(spec=BranchingRule)
    branching_rule.get_children.return_value = []
    config = replace(build_scripted_config(), branching_rule=branching_rule)

    FakeBranchAndPriceSolver(config).solve(ProblemData())

    ((root, evaluation),) = [
        called.args for called in branching_rule.get_children.call_args_list
    ]
    assert root.branching_decisions == ()
    assert evaluation.relaxation_solution == {
        FakeColumn(cost=ROOT_OBJECTIVE, key=(1,)): 1.0
    }


def test_the_node_lower_bound_generator_sets_the_node_bound() -> None:
    meta_data = solve_scripted_tree(
        node_lower_bound_generator=IncrementedLowerBoundGenerator()
    )

    assert meta_data["root_bound"] == ROOT_OBJECTIVE + 1.0


def test_an_integral_node_is_judged_by_its_objective_not_by_its_bound() -> None:
    # the second child's bound, 12, reaches the first child's incumbent, 12, yet its
    # own objective, 11, improves it
    meta_data = solve_scripted_tree(
        node_lower_bound_generator=IncrementedLowerBoundGenerator()
    )

    assert meta_data["objective"] == min(CHILD_OBJECTIVES)
    assert meta_data["explored_node_count"] == 3


def test_a_heuristic_incumbent_closes_the_tree_and_is_extracted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    extract_solution = Mock(return_value=Solution())
    monkeypatch.setattr(FakeBranchAndPriceSolver, "_extract_solution", extract_solution)

    meta_data = solve_scripted_tree(
        node_incumbent_generator=ScriptedIncumbentGenerator()
    )

    assert meta_data["status"] == "optimal"
    assert meta_data["objective"] == HEURISTIC_OBJECTIVE
    extract_solution.assert_called_once_with(HEURISTIC_COLUMN_VALUES)


def build_evaluation(
    integral: bool = False,
    lower_bound: float = 8.0,
    incumbent_objective: float | None = None,
) -> NodeEvaluation:
    incumbent = None
    if incumbent_objective is not None:
        incumbent = Incumbent(incumbent_objective, HEURISTIC_COLUMN_VALUES)

    return NodeEvaluation(
        feasible=True,
        relaxation_objective=lower_bound,
        lower_bound=lower_bound,
        relaxation_solution={},
        integral=integral,
        incumbent=incumbent,
    )


INFEASIBLE_EVALUATION = NodeEvaluation(
    feasible=False,
    relaxation_objective=math.inf,
    lower_bound=math.inf,
    relaxation_solution={},
    integral=False,
    incumbent=None,
)


@pytest.mark.parametrize(
    ("evaluation", "outcome", "incumbent_objective"),
    [
        (INFEASIBLE_EVALUATION, NodeOutcome.INFEASIBLE, 10.0),
        (build_evaluation(True, 9.0, 9.0), NodeOutcome.INTEGRAL, 9.0),
        (build_evaluation(True, 11.0, 11.0), NodeOutcome.PRUNED, 10.0),
        (build_evaluation(lower_bound=11.0), NodeOutcome.PRUNED, 10.0),
        (build_evaluation(incumbent_objective=8.0), NodeOutcome.HEURISTIC, 8.0),
        (build_evaluation(incumbent_objective=9.0), NodeOutcome.BRANCHED, 9.0),
        (build_evaluation(), NodeOutcome.BRANCHED, 10.0),
    ],
)
def test_settling_a_node_takes_an_improving_incumbent_and_decides_its_outcome(
    evaluation: NodeEvaluation, outcome: NodeOutcome, incumbent_objective: float
) -> None:
    solver = FakeBranchAndPriceSolver(build_scripted_config())
    solver._incumbent = Incumbent(10.0, {})

    assert solver._settle_node(evaluation) is outcome
    assert solver._get_incumbent_objective() == incumbent_objective

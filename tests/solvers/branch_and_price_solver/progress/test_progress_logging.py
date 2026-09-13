import logging
import math
from dataclasses import replace

import pytest

from template.model.data.problem_data import ProblemData
from template.model.solve_result import SolveResult
from template.solvers.branch_and_price_solver.branch_and_price_observer import (
    BranchAndPriceObserver,
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
from template.solvers.branch_and_price_solver.column_generation.column_pool import (
    ColumnPool,
)
from template.solvers.branch_and_price_solver.column_generation.master.master_problem import (
    MasterProblem,
)
from template.solvers.branch_and_price_solver.column_generation.pricing.pricing_problem import (
    PricingProblem,
)
from template.solvers.branch_and_price_solver.explored_node import ExploredNode
from template.solvers.branch_and_price_solver.node_outcome import NodeOutcome
from template.solvers.branch_and_price_solver.progress import progress_logging
from template.solvers.branch_and_price_solver.progress.node_component import (
    NodeComponent,
)
from template.solvers.branch_and_price_solver.progress.node_observations import (
    NodeObservations,
)
from template.solvers.branch_and_price_solver.progress.node_record import NodeRecord
from template.solvers.branch_and_price_solver.progress.progress_logging import (
    ProgressLogging,
)
from template.solvers.branch_and_price_solver.progress.progress_table import (
    SUMMARY_PREFIX,
    ProgressTable,
)
from template.solvers.branch_and_price_solver.progress.timed_column_generation import (
    TimedColumnGeneration,
)
from tests.solvers.branch_and_price_solver import (
    test_branch_and_price_solver as solver_tests,
)
from tests.solvers.branch_and_price_solver.test_branch_and_price_solver import (
    FakeBranchAndPriceSolver,
    FakeColumn,
    FakeMasterProblem,
    NullPricingProblem,
    build_scripted_config,
)

INFEASIBLE_RECORD = NodeRecord(
    node_id=6,
    depth=2,
    compatible_column_count=142,
    round_count=0,
    new_column_count=0,
    lower_bound=math.inf,
    outcome=NodeOutcome.INFEASIBLE,
    child_count=0,
    integral=None,
    seconds_by_component={
        NodeComponent.MASTER: 0.011,
        NodeComponent.PRICING: 0.009,
        NodeComponent.COLUMN_GENERATION: 0.052,
    },
    node_seconds=0.072,
    elapsed_seconds=3.2,
    incumbent_objective=1049.5,
    best_bound=1049.0,
)

SCRIPTED_ROUND_COUNT = 3
SCRIPTED_NEW_COLUMNS: list[Column] = [
    FakeColumn(cost=1.0, key=(1,)),
    FakeColumn(cost=2.0, key=(2,)),
]


class RecordingObserver(BranchAndPriceObserver):
    """Keeps what the solver reported, for the assertions."""

    explored_nodes: list[ExploredNode]
    started_at: list[float]
    result: SolveResult | None

    def __init__(self) -> None:
        self.explored_nodes = []
        self.started_at = []
        self.result = None

    def on_search_started(self, started_at: float) -> None:
        self.started_at.append(started_at)

    def on_node_explored(self, explored: ExploredNode) -> None:
        self.explored_nodes.append(explored)

    def on_search_finished(self, result: SolveResult) -> None:
        self.result = result


class ScriptedColumnGeneration(ColumnGeneration):
    """Fills the pool with the scripted columns and reports the scripted rounds."""

    def run(
        self,
        master: MasterProblem,
        pricing_problem: PricingProblem,
        column_pool: ColumnPool,
    ) -> ColumnGenerationResult:
        column_pool.add(SCRIPTED_NEW_COLUMNS)

        return ColumnGenerationResult(
            status=ColumnGenerationStatus.CONVERGED,
            bound=1.0,
            round_count=SCRIPTED_ROUND_COUNT,
        )


def get_node_rows(messages: list[str]) -> list[str]:
    header_lines = ProgressTable.format_header().splitlines()

    rows: list[str] = []
    for message in messages:
        if message in header_lines:
            continue
        if message.startswith(SUMMARY_PREFIX):
            continue

        rows.append(message)

    return rows


def test_the_logging_writes_one_row_per_node_under_a_single_header(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO)
    config = ProgressLogging().wrap(build_scripted_config(monkeypatch))

    FakeBranchAndPriceSolver(config).solve(ProblemData())

    messages = [record.getMessage() for record in caplog.records]
    header_lines = ProgressTable.format_header().splitlines()
    assert [line for line in messages if line in header_lines] == header_lines
    rows = get_node_rows(messages)
    assert [row.startswith("*") for row in rows] == [False, True, True]
    assert messages[-1].startswith(f"{SUMMARY_PREFIX}: objective 11.00")


def test_every_explored_node_reaches_the_observer_with_its_outcome(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observer = RecordingObserver()
    config = replace(build_scripted_config(monkeypatch), observers=[observer])

    result = FakeBranchAndPriceSolver(config).solve(ProblemData())

    assert [explored.outcome for explored in observer.explored_nodes] == [
        NodeOutcome.BRANCHED,
        NodeOutcome.INTEGRAL,
        NodeOutcome.INTEGRAL,
    ]
    assert len(observer.started_at) == 1
    assert observer.result is result


def test_a_row_prints_dashes_for_the_components_the_node_never_reached() -> None:
    assert ProgressTable.format_row(INFEASIBLE_RECORD) == (
        "X   6      2 |   142      0    0      inf "
        "|   1049.50   1049.00  0.0% |  0.011   0.009  0.052"
        "     -     -      -      - 0.072     3.20"
    )


def test_the_timed_column_generation_records_the_rounds_and_the_new_columns() -> None:
    observations = NodeObservations()
    column_pool = ColumnPool()
    column_pool.add([FakeColumn(cost=0.0, key=(0,))])

    TimedColumnGeneration(ScriptedColumnGeneration(), observations).run(
        FakeMasterProblem(1.0), NullPricingProblem(), column_pool
    )

    assert observations.round_count == SCRIPTED_ROUND_COUNT
    assert observations.new_column_count == len(SCRIPTED_NEW_COLUMNS)
    assert observations.seconds_by_component[NodeComponent.COLUMN_GENERATION] >= 0.0


def test_zero_objective_logging_does_not_crash_when_info_is_disabled(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(solver_tests, "ROOT_OBJECTIVE", 0.0)
    monkeypatch.setattr(solver_tests, "CHILD_OBJECTIVES", (0.0, 0.0))
    caplog.set_level(logging.WARNING)

    config = ProgressLogging().wrap(build_scripted_config(monkeypatch))

    result = FakeBranchAndPriceSolver(config).solve(ProblemData())

    assert result.meta_data["objective"] == 0.0


def test_zero_objective_gap_has_explicit_values() -> None:
    assert ProgressTable._format_gap(0.0, 0.0) == "0.0%"
    assert ProgressTable._format_gap(0.0, -1.0) == "inf"


def test_progress_logging_resets_for_each_search(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO)
    progress = ProgressLogging()

    first_config = progress.wrap(build_scripted_config(monkeypatch))
    FakeBranchAndPriceSolver(first_config).solve(ProblemData())
    first_messages = [record.getMessage() for record in caplog.records]

    caplog.clear()
    second_config = progress.wrap(build_scripted_config(monkeypatch))
    FakeBranchAndPriceSolver(second_config).solve(ProblemData())
    second_messages = [record.getMessage() for record in caplog.records]

    header_lines = ProgressTable.format_header().splitlines()
    assert [line for line in first_messages if line in header_lines] == header_lines
    assert [line for line in second_messages if line in header_lines] == header_lines
    assert get_node_rows(first_messages)[0][1:5].strip() == "1"
    assert get_node_rows(second_messages)[0][1:5].strip() == "1"


def test_progress_logging_uses_the_solver_start_time_for_elapsed_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    progress = ProgressLogging()
    records: list[NodeRecord] = []
    monkeypatch.setattr(progress._logger, "log_node", records.append)
    monkeypatch.setattr(progress_logging, "perf_counter", lambda: 20.0)

    progress.on_search_started(10.0)
    progress.on_search_started(15.0)
    progress.on_node_explored(
        ExploredNode(
            node=solver_tests.ROOT_NODE,
            outcome=NodeOutcome.INFEASIBLE,
            incumbent_objective=math.inf,
            best_bound=math.inf,
        )
    )

    assert records[0].elapsed_seconds == 5.0


def test_progress_table_reports_integrality_for_a_pruned_integral_node(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(solver_tests, "ROOT_OBJECTIVE", 0.0)
    monkeypatch.setattr(solver_tests, "CHILD_OBJECTIVES", (10.0, 10.0))
    caplog.set_level(logging.DEBUG)

    observer = RecordingObserver()
    config = replace(build_scripted_config(monkeypatch), observers=[observer])
    config = ProgressLogging().wrap(config)

    FakeBranchAndPriceSolver(config).solve(ProblemData())

    assert [explored.outcome for explored in observer.explored_nodes] == [
        NodeOutcome.BRANCHED,
        NodeOutcome.INTEGRAL,
        NodeOutcome.PRUNED,
    ]
    node_blocks = [
        record.getMessage()
        for record in caplog.records
        if record.getMessage().startswith("node ")
    ]
    integrality_line = next(
        line
        for line in node_blocks[-1].splitlines()
        if line.startswith("  integrality")
    )
    assert "integral" in integrality_line
    assert "fractional" not in integrality_line

import logging
import math
from dataclasses import replace
from unittest.mock import Mock

import pytest

from template.model.data.problem_data import ProblemData
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
from template.solvers.branch_and_price_solver.column_generation.column_generation_result import (
    ColumnGenerationResult,
)
from template.solvers.branch_and_price_solver.column_generation.column_generation_status import (
    ColumnGenerationStatus,
)
from template.solvers.branch_and_price_solver.explored_node import ExploredNode
from template.solvers.branch_and_price_solver.node_evaluation import NodeEvaluation
from template.solvers.branch_and_price_solver.node_outcome import NodeOutcome
from template.solvers.branch_and_price_solver.progress.progress_logger import (
    ProgressLogger,
)
from template.solvers.branch_and_price_solver.progress.progress_table import (
    SUMMARY_PREFIX,
    ProgressTable,
)
from template.solvers.branch_and_price_solver.search_summary import SearchSummary
from template.solvers.branch_and_price_solver.timing.node_step import NodeStep
from tests.solvers.branch_and_price_solver.test_branch_and_price_solver import (
    FakeClock,
    NodeDurationObserver,
    build_scripted_config,
)

INFEASIBLE_NODE = ExploredNode(
    node_id=6,
    node=BranchNode(
        branching_decisions=(
            Mock(spec=BranchingDecision),
            Mock(spec=BranchingDecision),
        ),
        lower_bound=math.inf,
    ),
    outcome=NodeOutcome.INFEASIBLE,
    compatible_column_count=142,
    column_generation_result=ColumnGenerationResult(
        status=ColumnGenerationStatus.INFEASIBLE,
        relaxation_objective=math.inf,
        round_count=4,
        new_column_count=7,
    ),
    evaluation=NodeEvaluation(
        feasible=False,
        relaxation_objective=math.inf,
        lower_bound=math.inf,
        relaxation_solution={},
        integral=False,
        incumbent=None,
    ),
    child_count=0,
    seconds_by_step={
        NodeStep.BUILD_MASTER: 0.011,
        NodeStep.BUILD_PRICING: 0.009,
        NodeStep.MASTER_SOLVE: 0.030,
        NodeStep.PRICING: 0.020,
        NodeStep.COLUMN_GENERATION: 0.002,
    },
    elapsed_seconds=3.2,
    incumbent_objective=1049.5,
    best_bound=1049.0,
)


class RecordingObserver(BranchAndPriceObserver):
    """Keeps what the solver reported, for the assertions."""

    explored_nodes: list[ExploredNode]
    summary: SearchSummary | None

    def __init__(self) -> None:
        self.explored_nodes = []
        self.summary = None

    def on_node_explored(self, explored: ExploredNode) -> None:
        self.explored_nodes.append(explored)

    def on_search_finished(self, summary: SearchSummary) -> None:
        self.summary = summary


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
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO)
    config = replace(build_scripted_config(), observers=[ProgressLogger()])

    BranchAndPriceSolver(config).solve(ProblemData())

    messages = [record.getMessage() for record in caplog.records]
    header_lines = ProgressTable.format_header().splitlines()
    assert [line for line in messages if line in header_lines] == header_lines
    rows = get_node_rows(messages)
    assert [row.lstrip().startswith("*") for row in rows] == [False, True, True]
    assert messages[-1].startswith(f"{SUMMARY_PREFIX}: objective 11.00")


def test_every_explored_node_and_the_summary_reach_the_observer() -> None:
    observer = RecordingObserver()
    config = replace(build_scripted_config(), observers=[observer])

    result = BranchAndPriceSolver(config).solve(ProblemData())

    assert [explored.node_id for explored in observer.explored_nodes] == [1, 2, 3]
    assert [explored.outcome for explored in observer.explored_nodes] == [
        NodeOutcome.BRANCHED,
        NodeOutcome.INTEGRAL,
        NodeOutcome.INTEGRAL,
    ]
    assert observer.summary is not None
    assert observer.summary.objective == result.meta_data["objective"] == 11.0
    assert observer.summary.explored_node_count == 3


def test_explored_nodes_report_the_elapsed_time_since_the_search_started() -> None:
    clock = FakeClock()
    clock.now = 100.0
    observer = RecordingObserver()
    config = replace(
        build_scripted_config(),
        clock=clock,
        observers=[observer, NodeDurationObserver(clock, node_seconds=60.0)],
    )

    BranchAndPriceSolver(config).solve(ProblemData())

    assert [explored.elapsed_seconds for explored in observer.explored_nodes] == [
        0.0,
        60.0,
        120.0,
    ]


def test_a_row_prints_dashes_for_the_steps_the_node_never_reached() -> None:
    assert ProgressTable.format_row(INFEASIBLE_NODE) == (
        " X  6    2    |  142    4     7     inf    "
        "|  1049.50   1049.00   0.0% "
        "|  0.011   0.009  0.030   0.020  0.002    -     -     -      -  "
        "  0.072   3.20"
    )


def test_the_debug_block_reports_only_the_steps_the_node_reached() -> None:
    lines = ProgressTable.format_debug_block(INFEASIBLE_NODE).splitlines()

    assert lines[0] == "node 6  depth 2"
    assert lines[2].split() == ["build", "master", "142", "columns", "0.011"]
    assert lines[6].split() == ["column", "generation", "infeasible", "0.002"]
    assert lines[7].split() == ["lower", "bound", "-"]
    assert lines[-1].split() == ["total", "0.072"]


def test_zero_objective_logging_does_not_crash_when_info_is_disabled(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING)
    config = replace(
        build_scripted_config(root_objective=0.0, child_objectives=(0.0, 0.0)),
        observers=[ProgressLogger()],
    )

    result = BranchAndPriceSolver(config).solve(ProblemData())

    assert result.meta_data["objective"] == 0.0


def test_zero_objective_gap_has_explicit_values() -> None:
    assert ProgressTable._format_gap(0.0, 0.0) == "0.0%"
    assert ProgressTable._format_gap(0.0, -1.0) == "inf"


def test_one_progress_logger_restarts_the_header_and_ids_for_each_search(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO)
    progress_logger = ProgressLogger()

    first_config = replace(build_scripted_config(), observers=[progress_logger])
    BranchAndPriceSolver(first_config).solve(ProblemData())
    first_messages = [record.getMessage() for record in caplog.records]

    caplog.clear()
    second_config = replace(build_scripted_config(), observers=[progress_logger])
    BranchAndPriceSolver(second_config).solve(ProblemData())
    second_messages = [record.getMessage() for record in caplog.records]

    header_lines = ProgressTable.format_header().splitlines()
    assert [line for line in first_messages if line in header_lines] == header_lines
    assert [line for line in second_messages if line in header_lines] == header_lines
    assert get_node_rows(first_messages)[0][1:5].strip() == "1"
    assert get_node_rows(second_messages)[0][1:5].strip() == "1"


def test_progress_table_reports_integrality_for_a_pruned_integral_node(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    observer = RecordingObserver()
    config = replace(
        build_scripted_config(root_objective=0.0, child_objectives=(10.0, 10.0)),
        observers=[observer, ProgressLogger()],
    )

    BranchAndPriceSolver(config).solve(ProblemData())

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

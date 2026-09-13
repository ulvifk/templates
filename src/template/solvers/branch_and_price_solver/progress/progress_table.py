import math

from template.solvers.branch_and_price_solver.node_outcome import NodeOutcome
from template.solvers.branch_and_price_solver.progress.node_component import (
    NodeComponent,
)
from template.solvers.branch_and_price_solver.progress.node_record import NodeRecord

GROUP_SEPARATOR = " |"
MISSING_CELL = "-"
SUMMARY_PREFIX = "branch-and-price finished"

GROUP_TITLES = ("Nodes", "Current Node", "Objective Bounds", "Time (s)")

MARKER_BY_OUTCOME = {
    NodeOutcome.BRANCHED: "",
    NodeOutcome.PRUNED: "",
    NodeOutcome.INTEGRAL: "*",
    NodeOutcome.HEURISTIC: "H",
    NodeOutcome.INFEASIBLE: "X",
}

MARKER_WIDTH = 1
NODE_ID_WIDTH = 4
DEPTH_WIDTH = 7

COMPATIBLE_COLUMN_COUNT_WIDTH = 6
ROUND_COUNT_WIDTH = 7
NEW_COLUMN_COUNT_WIDTH = 5
NODE_LOWER_BOUND_WIDTH = 9

INCUMBENT_WIDTH = 10
BEST_BOUND_WIDTH = 10
GAP_WIDTH = 6

MASTER_SECONDS_WIDTH = 7
PRICING_SECONDS_WIDTH = 8
COLUMN_GENERATION_SECONDS_WIDTH = 7
LOWER_BOUND_SECONDS_WIDTH = 6
INTEGRALITY_SECONDS_WIDTH = 6
INCUMBENT_SECONDS_WIDTH = 7
BRANCHING_SECONDS_WIDTH = 7
NODE_SECONDS_WIDTH = 6
ELAPSED_SECONDS_WIDTH = 9

DEBUG_INDENT = "  "
DEBUG_COMPONENT_WIDTH = 21
DEBUG_RESULT_WIDTH = 36
DEBUG_TIME_WIDTH = 8


class ProgressTable:
    """Renders node records as the progress table rows the logger writes."""

    @staticmethod
    def format_header() -> str:
        groups = [
            [
                (MARKER_WIDTH, ""),
                (NODE_ID_WIDTH, "id"),
                (DEPTH_WIDTH, "depth"),
            ],
            [
                (COMPATIBLE_COLUMN_COUNT_WIDTH, "cols"),
                (ROUND_COUNT_WIDTH, "rounds"),
                (NEW_COLUMN_COUNT_WIDTH, "new"),
                (NODE_LOWER_BOUND_WIDTH, "node_lb"),
            ],
            [
                (INCUMBENT_WIDTH, "incumbent"),
                (BEST_BOUND_WIDTH, "best_bd"),
                (GAP_WIDTH, "gap"),
            ],
            [
                (MASTER_SECONDS_WIDTH, "master"),
                (PRICING_SECONDS_WIDTH, "pricing"),
                (COLUMN_GENERATION_SECONDS_WIDTH, "colgen"),
                (LOWER_BOUND_SECONDS_WIDTH, "lb"),
                (INTEGRALITY_SECONDS_WIDTH, "integ"),
                (INCUMBENT_SECONDS_WIDTH, "incumb"),
                (BRANCHING_SECONDS_WIDTH, "branch"),
                (NODE_SECONDS_WIDTH, "node"),
                (ELAPSED_SECONDS_WIDTH, "elapsed"),
            ],
        ]

        return f"{ProgressTable._format_titles(groups)}\n{ProgressTable._format_groups(groups)}"

    @staticmethod
    def format_row(record: NodeRecord) -> str:
        groups = [
            [
                (MARKER_WIDTH, MARKER_BY_OUTCOME[record.outcome]),
                (NODE_ID_WIDTH, str(record.node_id)),
                (DEPTH_WIDTH, str(record.depth)),
            ],
            [
                (COMPATIBLE_COLUMN_COUNT_WIDTH, str(record.compatible_column_count)),
                (ROUND_COUNT_WIDTH, str(record.round_count)),
                (NEW_COLUMN_COUNT_WIDTH, str(record.new_column_count)),
                (
                    NODE_LOWER_BOUND_WIDTH,
                    ProgressTable._format_objective(record.lower_bound),
                ),
            ],
            [
                (
                    INCUMBENT_WIDTH,
                    ProgressTable._format_objective(record.incumbent_objective),
                ),
                (BEST_BOUND_WIDTH, ProgressTable._format_objective(record.best_bound)),
                (
                    GAP_WIDTH,
                    ProgressTable._format_gap(
                        record.incumbent_objective, record.best_bound
                    ),
                ),
            ],
            [
                (
                    MASTER_SECONDS_WIDTH,
                    ProgressTable._format_component_seconds(
                        record, NodeComponent.MASTER
                    ),
                ),
                (
                    PRICING_SECONDS_WIDTH,
                    ProgressTable._format_component_seconds(
                        record, NodeComponent.PRICING
                    ),
                ),
                (
                    COLUMN_GENERATION_SECONDS_WIDTH,
                    ProgressTable._format_component_seconds(
                        record, NodeComponent.COLUMN_GENERATION
                    ),
                ),
                (
                    LOWER_BOUND_SECONDS_WIDTH,
                    ProgressTable._format_component_seconds(
                        record, NodeComponent.LOWER_BOUND
                    ),
                ),
                (
                    INTEGRALITY_SECONDS_WIDTH,
                    ProgressTable._format_component_seconds(
                        record, NodeComponent.INTEGRALITY
                    ),
                ),
                (
                    INCUMBENT_SECONDS_WIDTH,
                    ProgressTable._format_component_seconds(
                        record, NodeComponent.INCUMBENT
                    ),
                ),
                (
                    BRANCHING_SECONDS_WIDTH,
                    ProgressTable._format_component_seconds(
                        record, NodeComponent.BRANCHING
                    ),
                ),
                (
                    NODE_SECONDS_WIDTH,
                    ProgressTable._format_seconds(record.node_seconds),
                ),
                (ELAPSED_SECONDS_WIDTH, f"{record.elapsed_seconds:.2f}"),
            ],
        ]

        return ProgressTable._format_groups(groups)

    @staticmethod
    def format_debug_block(record: NodeRecord) -> str:
        components = [
            (
                "master builder",
                NodeComponent.MASTER,
                f"{record.compatible_column_count} columns",
            ),
            ("pricing builder", NodeComponent.PRICING, ""),
            (
                "column generation",
                NodeComponent.COLUMN_GENERATION,
                ProgressTable._get_column_generation_result(record),
            ),
            (
                "lower bound",
                NodeComponent.LOWER_BOUND,
                ProgressTable._format_objective(record.lower_bound),
            ),
            (
                "integrality",
                NodeComponent.INTEGRALITY,
                ProgressTable._get_integrality_result(record),
            ),
            (
                "incumbent generator",
                NodeComponent.INCUMBENT,
                ProgressTable._get_incumbent_result(record),
            ),
            ("branching", NodeComponent.BRANCHING, f"{record.child_count} children"),
        ]

        lines = [
            f"node {record.node_id}  depth {record.depth}",
            ProgressTable._format_debug_line("component", "result", "time (s)"),
        ]
        for label, component, result in components:
            ran = component in record.seconds_by_component
            lines.append(
                ProgressTable._format_debug_line(
                    label,
                    result if ran else "",
                    ProgressTable._format_component_seconds(record, component),
                )
            )
        lines.append(
            ProgressTable._format_debug_line(
                "total", "", ProgressTable._format_seconds(record.node_seconds)
            )
        )

        return "\n".join(lines)

    @staticmethod
    def format_summary(
        objective: float,
        best_bound: float,
        explored_node_count: int,
        runtime_seconds: float,
    ) -> str:
        formatted_objective = ProgressTable._format_objective(objective)
        formatted_bound = ProgressTable._format_objective(best_bound)
        gap = ProgressTable._format_gap(objective, best_bound)

        return (
            f"{SUMMARY_PREFIX}: objective {formatted_objective}"
            f"  best bound {formatted_bound}  gap {gap}"
            f"  nodes {explored_node_count}  time {runtime_seconds:.2f}s"
        )

    @staticmethod
    def _format_titles(groups: list[list[tuple[int, str]]]) -> str:
        titles = []
        for title, cells in zip(GROUP_TITLES, groups, strict=True):
            group_width = sum(width for width, _ in cells)
            titles.append(title.center(group_width))

        return GROUP_SEPARATOR.join(titles).rstrip()

    @staticmethod
    def _format_groups(groups: list[list[tuple[int, str]]]) -> str:
        formatted_groups = []
        for cells in groups:
            formatted_cells = [text.rjust(width) for width, text in cells]
            formatted_groups.append("".join(formatted_cells))

        return GROUP_SEPARATOR.join(formatted_groups)

    @staticmethod
    def _format_debug_line(label: str, result: str, time_text: str) -> str:
        return (
            f"{DEBUG_INDENT}{label.ljust(DEBUG_COMPONENT_WIDTH)}"
            f"{result.ljust(DEBUG_RESULT_WIDTH)}{time_text.rjust(DEBUG_TIME_WIDTH)}"
        ).rstrip()

    @staticmethod
    def _format_component_seconds(record: NodeRecord, component: NodeComponent) -> str:
        if component not in record.seconds_by_component:
            return MISSING_CELL

        return ProgressTable._format_seconds(record.seconds_by_component[component])

    @staticmethod
    def _format_objective(value: float) -> str:
        return f"{value:.2f}"

    @staticmethod
    def _format_seconds(value: float) -> str:
        return f"{value:.3f}"

    @staticmethod
    def _format_gap(incumbent_objective: float, best_bound: float) -> str:
        if math.isinf(incumbent_objective):
            return MISSING_CELL
        if incumbent_objective == 0.0:
            if best_bound == 0.0:
                return "0.0%"

            return "inf"

        gap = (incumbent_objective - best_bound) / abs(incumbent_objective)

        return f"{100.0 * gap:.1f}%"

    @staticmethod
    def _get_column_generation_result(record: NodeRecord) -> str:
        if record.outcome is NodeOutcome.INFEASIBLE:
            return "infeasible"

        return f"converged, {record.round_count} rounds, {record.new_column_count} new columns"

    @staticmethod
    def _get_integrality_result(record: NodeRecord) -> str:
        if record.integral is None:
            return ""
        if record.integral:
            return "integral"

        return "fractional"

    @staticmethod
    def _get_incumbent_result(record: NodeRecord) -> str:
        if record.outcome is not NodeOutcome.HEURISTIC:
            return ""

        return f"found {ProgressTable._format_objective(record.incumbent_objective)}"

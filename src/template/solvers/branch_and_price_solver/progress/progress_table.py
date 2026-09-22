import math

from template.solvers.branch_and_price_solver.explored_node import ExploredNode
from template.solvers.branch_and_price_solver.node_outcome import NodeOutcome
from template.solvers.branch_and_price_solver.search_summary import SearchSummary
from template.solvers.branch_and_price_solver.timing.node_step import NodeStep

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

MARKER_WIDTH = 2
NODE_ID_WIDTH = 4
DEPTH_WIDTH = 7

COMPATIBLE_COLUMN_COUNT_WIDTH = 6
ROUND_COUNT_WIDTH = 7
NEW_COLUMN_COUNT_WIDTH = 5
NODE_LOWER_BOUND_WIDTH = 9

INCUMBENT_WIDTH = 10
BEST_BOUND_WIDTH = 10
GAP_WIDTH = 6

STEP_SECONDS_MIN_WIDTH = 6  # a step column fits its header and one space, at least
NODE_SECONDS_WIDTH = 6
ELAPSED_SECONDS_WIDTH = 9

DEBUG_INDENT = "  "
DEBUG_STEP_WIDTH = 21
DEBUG_RESULT_WIDTH = 36
DEBUG_TIME_WIDTH = 8


class ProgressTable:
    """Renders explored nodes as the progress table rows the logger writes."""

    @staticmethod
    def format_header() -> str:
        step_cells = [
            (ProgressTable._get_step_width(step), step.value) for step in NodeStep
        ]
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
                *step_cells,
                (NODE_SECONDS_WIDTH, "node"),
                (ELAPSED_SECONDS_WIDTH, "elapsed"),
            ],
        ]

        return f"{ProgressTable._format_titles(groups)}\n{ProgressTable._format_groups(groups)}"

    @staticmethod
    def format_row(explored: ExploredNode) -> str:
        column_generation_result = explored.column_generation_result
        step_cells = [
            (
                ProgressTable._get_step_width(step),
                ProgressTable._format_step_seconds(explored, step),
            )
            for step in NodeStep
        ]
        groups = [
            [
                (MARKER_WIDTH, MARKER_BY_OUTCOME[explored.outcome]),
                (NODE_ID_WIDTH, str(explored.node_id)),
                (DEPTH_WIDTH, str(ProgressTable._get_depth(explored))),
            ],
            [
                (COMPATIBLE_COLUMN_COUNT_WIDTH, str(explored.compatible_column_count)),
                (ROUND_COUNT_WIDTH, str(column_generation_result.round_count)),
                (
                    NEW_COLUMN_COUNT_WIDTH,
                    str(column_generation_result.new_column_count),
                ),
                (
                    NODE_LOWER_BOUND_WIDTH,
                    ProgressTable._format_objective(explored.node.lower_bound),
                ),
            ],
            [
                (
                    INCUMBENT_WIDTH,
                    ProgressTable._format_objective(explored.incumbent_objective),
                ),
                (
                    BEST_BOUND_WIDTH,
                    ProgressTable._format_objective(explored.best_bound),
                ),
                (
                    GAP_WIDTH,
                    ProgressTable._format_gap(
                        explored.incumbent_objective, explored.best_bound
                    ),
                ),
            ],
            [
                *step_cells,
                (
                    NODE_SECONDS_WIDTH,
                    ProgressTable._format_seconds(
                        ProgressTable._get_node_seconds(explored)
                    ),
                ),
                (ELAPSED_SECONDS_WIDTH, f"{explored.elapsed_seconds:.2f}"),
            ],
        ]

        return ProgressTable._format_groups(groups)

    @staticmethod
    def format_debug_block(explored: ExploredNode) -> str:
        result_by_step = ProgressTable._get_result_by_step(explored)

        lines = [
            f"node {explored.node_id}  depth {ProgressTable._get_depth(explored)}",
            ProgressTable._format_debug_line("step", "result", "time (s)"),
        ]
        for step in NodeStep:
            result = ""
            if step in explored.seconds_by_step:
                result = result_by_step.get(step, "")
            lines.append(
                ProgressTable._format_debug_line(
                    ProgressTable._get_step_label(step),
                    result,
                    ProgressTable._format_step_seconds(explored, step),
                )
            )
        lines.append(
            ProgressTable._format_debug_line(
                "total",
                "",
                ProgressTable._format_seconds(
                    ProgressTable._get_node_seconds(explored)
                ),
            )
        )

        return "\n".join(lines)

    @staticmethod
    def format_summary(summary: SearchSummary) -> str:
        formatted_objective = ProgressTable._format_objective(summary.objective)
        formatted_bound = ProgressTable._format_objective(summary.best_bound)
        gap = ProgressTable._format_gap(summary.objective, summary.best_bound)

        return (
            f"{SUMMARY_PREFIX}: objective {formatted_objective}"
            f"  best bound {formatted_bound}  gap {gap}"
            f"  nodes {summary.explored_node_count}"
            f"  time {summary.runtime_seconds:.2f}s"
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
            # each width holds its cell and the space that separates it from the previous
            formatted_cells = [text.center(width - 1) for width, text in cells]
            formatted_groups.append(" " + " ".join(formatted_cells))

        return GROUP_SEPARATOR.join(formatted_groups).rstrip()

    @staticmethod
    def _format_debug_line(label: str, result: str, time_text: str) -> str:
        return (
            f"{DEBUG_INDENT}{label.ljust(DEBUG_STEP_WIDTH)}"
            f"{result.ljust(DEBUG_RESULT_WIDTH)}{time_text.rjust(DEBUG_TIME_WIDTH)}"
        ).rstrip()

    @staticmethod
    def _format_step_seconds(explored: ExploredNode, step: NodeStep) -> str:
        if step not in explored.seconds_by_step:
            return MISSING_CELL

        return ProgressTable._format_seconds(explored.seconds_by_step[step])

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
    def _get_step_width(step: NodeStep) -> int:
        return max(len(step.value) + 1, STEP_SECONDS_MIN_WIDTH)

    @staticmethod
    def _get_step_label(step: NodeStep) -> str:
        return step.name.lower().replace("_", " ")

    @staticmethod
    def _get_depth(explored: ExploredNode) -> int:
        return len(explored.node.branching_decisions)

    @staticmethod
    def _get_node_seconds(explored: ExploredNode) -> float:
        return sum(explored.seconds_by_step.values())

    # [step] -> what the step produced on the node; a step with nothing to report is absent
    @staticmethod
    def _get_result_by_step(explored: ExploredNode) -> dict[NodeStep, str]:
        column_generation_result = explored.column_generation_result

        return {
            NodeStep.BUILD_MASTER: f"{explored.compatible_column_count} columns",
            NodeStep.MASTER_SOLVE: f"{column_generation_result.round_count} rounds",
            NodeStep.PRICING: f"{column_generation_result.new_column_count} new columns",
            NodeStep.COLUMN_GENERATION: column_generation_result.status.value,
            NodeStep.LOWER_BOUND: ProgressTable._format_objective(
                explored.node.lower_bound
            ),
            NodeStep.INTEGRALITY: ProgressTable._get_integrality_result(explored),
            NodeStep.INCUMBENT: ProgressTable._get_incumbent_result(explored),
            NodeStep.BRANCHING: f"{explored.child_count} children",
        }

    @staticmethod
    def _get_integrality_result(explored: ExploredNode) -> str:
        if explored.node.integral:
            return "integral"

        return "fractional"

    @staticmethod
    def _get_incumbent_result(explored: ExploredNode) -> str:
        if explored.outcome is not NodeOutcome.HEURISTIC:
            return ""

        return f"found {ProgressTable._format_objective(explored.incumbent_objective)}"

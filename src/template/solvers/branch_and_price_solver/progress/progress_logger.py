import logging

from template.model.solve_result import SolveResult
from template.solvers.branch_and_price_solver.progress.node_record import NodeRecord
from template.solvers.branch_and_price_solver.progress.progress_table import (
    ProgressTable,
)

HEADER_ROW_INTERVAL = 20


class ProgressLogger:
    """Logs one table row per explored node, and a summary when the search ends."""

    _logger: logging.Logger
    _row_count: int

    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)
        self._row_count = 0

    def reset(self) -> None:
        self._row_count = 0

    def log_node(self, record: NodeRecord) -> None:
        if self._row_count % HEADER_ROW_INTERVAL == 0:
            for line in ProgressTable.format_header().splitlines():
                self._logger.info(line)
        self._row_count += 1

        self._logger.info(ProgressTable.format_row(record))
        self._logger.debug(ProgressTable.format_debug_block(record))

    def log_summary(self, result: SolveResult) -> None:
        meta_data = result.meta_data

        self._logger.info(
            ProgressTable.format_summary(
                meta_data["objective"],
                meta_data["best_bound"],
                meta_data["explored_node_count"],
                meta_data["runtime_seconds"],
            )
        )

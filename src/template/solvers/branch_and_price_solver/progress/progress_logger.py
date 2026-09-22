import logging

from template.solvers.branch_and_price_solver.branch_and_price_observer import (
    BranchAndPriceObserver,
)
from template.solvers.branch_and_price_solver.explored_node import ExploredNode
from template.solvers.branch_and_price_solver.progress.progress_table import (
    ProgressTable,
)
from template.solvers.branch_and_price_solver.search_summary import SearchSummary

HEADER_ROW_INTERVAL = 20


class ProgressLogger(BranchAndPriceObserver):
    """Logs one table row per explored node, and a summary when the search ends."""

    _logger: logging.Logger

    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)

    def on_node_explored(self, explored: ExploredNode) -> None:
        if (explored.node_id - 1) % HEADER_ROW_INTERVAL == 0:
            for line in ProgressTable.format_header().splitlines():
                self._logger.info(line)

        self._logger.info(ProgressTable.format_row(explored))
        self._logger.debug(ProgressTable.format_debug_block(explored))

    def on_search_finished(self, summary: SearchSummary) -> None:
        self._logger.info(ProgressTable.format_summary(summary))

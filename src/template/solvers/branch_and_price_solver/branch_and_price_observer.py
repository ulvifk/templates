from template.solvers.branch_and_price_solver.explored_node import ExploredNode
from template.solvers.branch_and_price_solver.search_summary import SearchSummary


class BranchAndPriceObserver:
    """Hears the search's progress; an observer overrides only the events it needs."""

    def on_node_explored(self, explored: ExploredNode) -> None:
        pass

    def on_search_finished(self, summary: SearchSummary) -> None:
        pass

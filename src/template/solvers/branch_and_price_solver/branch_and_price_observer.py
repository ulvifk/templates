from abc import ABC, abstractmethod

from template.model.solve_result import SolveResult
from template.solvers.branch_and_price_solver.explored_node import ExploredNode


class BranchAndPriceObserver(ABC):
    @abstractmethod
    def on_search_started(self, started_at: float) -> None: ...

    @abstractmethod
    def on_node_explored(self, explored: ExploredNode) -> None: ...

    @abstractmethod
    def on_search_finished(self, result: SolveResult) -> None: ...

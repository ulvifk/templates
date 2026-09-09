from abc import ABC, abstractmethod

from template.solvers.branch_and_price_solver.column_generation.column import Column
from template.solvers.branch_and_price_solver.column_generation.master.duals import (
    Duals,
)


class PricingProblem(ABC):
    # Return improving columns compatible with the node's decisions;
    # an empty list certifies pricing convergence for that node.
    @abstractmethod
    def price(self, duals: Duals) -> list[Column]: ...

    @abstractmethod
    def dispose(self) -> None: ...

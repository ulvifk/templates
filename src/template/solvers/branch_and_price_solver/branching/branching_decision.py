from abc import ABC, abstractmethod
from dataclasses import dataclass

from template.solvers.branch_and_price_solver.column_generation.column import Column


@dataclass(frozen=True, slots=True)
class BranchingDecision[M, P](ABC):
    """One branch choice that enforces itself; builders never inspect it."""

    # Whether the column may enter the node's master.
    @abstractmethod
    def is_column_compatible(self, column: Column) -> bool: ...

    # Enforce the choice on the master after its initial columns are in.
    @abstractmethod
    def apply_to_master(self, master: M) -> None: ...

    # Enforce the choice on pricing, including its reduced-cost calculation.
    @abstractmethod
    def apply_to_pricing(self, pricing_problem: P) -> None: ...

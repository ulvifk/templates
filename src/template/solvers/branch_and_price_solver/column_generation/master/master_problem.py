from abc import ABC, abstractmethod

from template.solvers.branch_and_price_solver.column_generation.column import Column
from template.solvers.branch_and_price_solver.column_generation.master.duals import (
    Duals,
)


class MasterProblem(ABC):
    """The restricted master; initialization and feasibility handling belong here."""

    @abstractmethod
    def add_columns(self, columns: list[Column]) -> None: ...

    # Return the optimal LP objective; never return an interrupted solve's objective.
    @abstractmethod
    def solve_relaxation(self) -> float: ...

    @abstractmethod
    def get_duals(self) -> Duals: ...

    # Called after pricing converges; report feasibility for the node's formulation.
    @abstractmethod
    def is_feasible(self) -> bool: ...

    # Called after pricing converges on a feasible node; whether the relaxation yields
    # a feasible integer solution with the same objective.
    @abstractmethod
    def is_integral(self) -> bool: ...

    @abstractmethod
    def get_master_relaxation_solution(self) -> dict[Column, float]: ...

    @abstractmethod
    def dispose(self) -> None: ...

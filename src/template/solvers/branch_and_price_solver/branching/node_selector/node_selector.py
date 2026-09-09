from abc import ABC, abstractmethod

from template.solvers.branch_and_price_solver.branching.branch_node import BranchNode


class NodeSelector(ABC):
    @abstractmethod
    def push(self, nodes: list[BranchNode]) -> None: ...

    @abstractmethod
    def pop(self) -> BranchNode | None: ...

    # math.inf when the selector is empty, so an exhausted tree bounds nothing
    @abstractmethod
    def get_best_lower_bound(self) -> float: ...

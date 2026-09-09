from abc import ABC, abstractmethod

from template.model.solution.solution import Solution


class Move(ABC):
    """One candidate change to a solution; gain is positive when the move improves it."""

    _gain: float | None

    def __init__(self) -> None:
        self._gain = None

    def get_gain(self) -> float:
        if self._gain is None:
            self._gain = self._compute_gain()

        return self._gain

    @abstractmethod
    def is_feasible(self) -> bool: ...

    @abstractmethod
    def apply(self) -> Solution: ...

    @abstractmethod
    def _compute_gain(self) -> float: ...

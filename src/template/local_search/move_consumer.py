from abc import ABC, abstractmethod

from template.constants import ZERO_TOLERANCE
from template.local_search.move import Move


class MoveConsumer(ABC):
    # accept returns whether the generator should keep scanning
    @abstractmethod
    def accept(self, move: Move) -> bool: ...


class BestMoveConsumer(MoveConsumer):
    _best_gain: float
    _best_move: Move | None

    def __init__(self) -> None:
        self._best_gain = ZERO_TOLERANCE
        self._best_move = None

    def accept(self, move: Move) -> bool:
        if not move.is_feasible():
            return True

        if move.get_gain() <= self._best_gain:
            return True

        self._best_gain = move.get_gain()
        self._best_move = move

        return True

    def get_best_move(self) -> Move | None:
        return self._best_move


class FirstMoveConsumer(MoveConsumer):
    _move: Move | None

    def __init__(self) -> None:
        self._move = None

    def accept(self, move: Move) -> bool:
        if not move.is_feasible():
            return True

        if move.get_gain() <= ZERO_TOLERANCE:
            return True

        self._move = move

        return False

    def get_move(self) -> Move | None:
        return self._move

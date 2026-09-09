from abc import ABC, abstractmethod

from template.local_search.move_consumer import BestMoveConsumer, FirstMoveConsumer
from template.local_search.move_generator import MoveGenerator
from template.model.solution.solution import Solution


class Neighborhood(ABC):
    # improve returns the very same solution object when no move improves it, so the
    # caller detects "no improvement" by identity
    @abstractmethod
    def improve(self, solution: Solution) -> Solution: ...


class BestImprovementNeighborhood(Neighborhood):
    _move_generator: MoveGenerator

    def __init__(self, move_generator: MoveGenerator) -> None:
        self._move_generator = move_generator

    def improve(self, solution: Solution) -> Solution:
        consumer = BestMoveConsumer()
        self._move_generator.for_each_move(solution, consumer)

        best_move = consumer.get_best_move()
        if best_move is None:
            return solution

        return best_move.apply()


class FirstImprovementNeighborhood(Neighborhood):
    _move_generator: MoveGenerator

    def __init__(self, move_generator: MoveGenerator) -> None:
        self._move_generator = move_generator

    def improve(self, solution: Solution) -> Solution:
        consumer = FirstMoveConsumer()
        self._move_generator.for_each_move(solution, consumer)

        move = consumer.get_move()
        if move is None:
            return solution

        return move.apply()

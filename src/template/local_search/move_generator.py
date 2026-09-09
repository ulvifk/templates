from abc import ABC, abstractmethod

from template.local_search.move_consumer import MoveConsumer
from template.model.solution.solution import Solution


class MoveGenerator(ABC):
    # for_each_move builds one move at a time and hands it to the consumer; it returns
    # as soon as accept answers False, so it never enumerates more moves than the
    # consumer asked for. Never build the full list.
    @abstractmethod
    def for_each_move(self, solution: Solution, consumer: MoveConsumer) -> None: ...

    # Example:
    #
    # class SwapMoveGenerator(MoveGenerator):
    #     _problem_data: ProblemData
    #
    #     def __init__(self, problem_data: ProblemData) -> None:
    #         self._problem_data = problem_data
    #
    #     def for_each_move(self, solution: Solution, consumer: MoveConsumer) -> None:
    #         sequence_length = len(solution.sequence)
    #
    #         for first in range(sequence_length):
    #             for second in range(first + 1, sequence_length):
    #                 move = SwapMove(self._problem_data, solution, first, second)
    #                 if not consumer.accept(move):
    #                     return

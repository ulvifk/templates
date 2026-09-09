from template.local_search.move import Move
from template.local_search.move_consumer import MoveConsumer
from template.local_search.move_generator import MoveGenerator
from template.local_search.neighborhood import (
    BestImprovementNeighborhood,
    FirstImprovementNeighborhood,
)
from template.model.solution.solution import Solution


class FakeMove(Move):
    result: Solution

    _feasible: bool
    _fake_gain: float

    def __init__(self, feasible: bool, gain: float) -> None:
        super().__init__()

        self.result = Solution()

        self._feasible = feasible
        self._fake_gain = gain

    def is_feasible(self) -> bool:
        return self._feasible

    def apply(self) -> Solution:
        return self.result

    def _compute_gain(self) -> float:
        return self._fake_gain


class FakeMoveGenerator(MoveGenerator):
    pushed_count: int

    _moves: list[FakeMove]

    def __init__(self, moves: list[FakeMove]) -> None:
        self.pushed_count = 0

        self._moves = moves

    def for_each_move(self, solution: Solution, consumer: MoveConsumer) -> None:
        for move in self._moves:
            self.pushed_count += 1

            if not consumer.accept(move):
                return


def test_best_improvement_returns_the_same_solution_when_nothing_improves() -> None:
    start = Solution()
    generator = FakeMoveGenerator(
        [FakeMove(feasible=True, gain=0.0), FakeMove(feasible=False, gain=9.0)]
    )
    neighborhood = BestImprovementNeighborhood(generator)

    assert neighborhood.improve(start) is start


def test_best_improvement_applies_the_highest_gain_move() -> None:
    best = FakeMove(feasible=True, gain=7.0)
    generator = FakeMoveGenerator([FakeMove(feasible=True, gain=1.0), best])
    neighborhood = BestImprovementNeighborhood(generator)

    assert neighborhood.improve(Solution()) is best.result


def test_best_improvement_scans_every_move() -> None:
    generator = FakeMoveGenerator(
        [FakeMove(feasible=True, gain=1.0), FakeMove(feasible=True, gain=7.0)]
    )
    neighborhood = BestImprovementNeighborhood(generator)

    neighborhood.improve(Solution())

    assert generator.pushed_count == 2


def test_first_improvement_returns_the_same_solution_when_nothing_improves() -> None:
    start = Solution()
    generator = FakeMoveGenerator([FakeMove(feasible=True, gain=0.0)])
    neighborhood = FirstImprovementNeighborhood(generator)

    assert neighborhood.improve(start) is start


def test_first_improvement_stops_pushing_at_the_first_improving_move() -> None:
    improving = FakeMove(feasible=True, gain=1.0)
    generator = FakeMoveGenerator(
        [
            FakeMove(feasible=True, gain=0.0),
            improving,
            FakeMove(feasible=True, gain=9.0),
        ]
    )
    neighborhood = FirstImprovementNeighborhood(generator)

    assert neighborhood.improve(Solution()) is improving.result
    assert generator.pushed_count == 2

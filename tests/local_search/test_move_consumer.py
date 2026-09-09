from template.local_search.move import Move
from template.local_search.move_consumer import BestMoveConsumer, FirstMoveConsumer
from template.model.solution.solution import Solution


class FakeMove(Move):
    _feasible: bool
    _fake_gain: float

    def __init__(self, feasible: bool, gain: float) -> None:
        super().__init__()

        self._feasible = feasible
        self._fake_gain = gain

    def is_feasible(self) -> bool:
        return self._feasible

    def apply(self) -> Solution:
        return Solution()

    def _compute_gain(self) -> float:
        return self._fake_gain


def test_best_consumer_keeps_the_highest_gain_move() -> None:
    best = FakeMove(feasible=True, gain=7.0)
    consumer = BestMoveConsumer()

    consumer.accept(FakeMove(feasible=True, gain=1.0))
    consumer.accept(best)
    consumer.accept(FakeMove(feasible=True, gain=3.0))

    assert consumer.get_best_move() is best


def test_best_consumer_skips_infeasible_moves() -> None:
    improving = FakeMove(feasible=True, gain=2.0)
    consumer = BestMoveConsumer()

    consumer.accept(FakeMove(feasible=False, gain=9.0))
    consumer.accept(improving)

    assert consumer.get_best_move() is improving


def test_best_consumer_returns_none_when_no_move_beats_the_tolerance() -> None:
    consumer = BestMoveConsumer()

    consumer.accept(FakeMove(feasible=True, gain=0.0))
    consumer.accept(FakeMove(feasible=True, gain=-1.0))

    assert consumer.get_best_move() is None


def test_best_consumer_always_asks_for_more_moves() -> None:
    consumer = BestMoveConsumer()

    assert consumer.accept(FakeMove(feasible=False, gain=9.0)) is True
    assert consumer.accept(FakeMove(feasible=True, gain=0.0)) is True
    assert consumer.accept(FakeMove(feasible=True, gain=5.0)) is True


def test_first_consumer_keeps_scanning_past_infeasible_and_non_improving_moves() -> (
    None
):
    consumer = FirstMoveConsumer()

    assert consumer.accept(FakeMove(feasible=False, gain=9.0)) is True
    assert consumer.accept(FakeMove(feasible=True, gain=0.0)) is True
    assert consumer.get_move() is None


def test_first_consumer_stops_the_scan_at_the_first_improving_move() -> None:
    improving = FakeMove(feasible=True, gain=1.0)
    consumer = FirstMoveConsumer()

    assert consumer.accept(improving) is False
    assert consumer.get_move() is improving

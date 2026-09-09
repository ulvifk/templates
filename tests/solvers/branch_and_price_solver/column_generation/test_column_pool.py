from collections.abc import Hashable
from dataclasses import dataclass

from template.solvers.branch_and_price_solver.column_generation.column import Column
from template.solvers.branch_and_price_solver.column_generation.column_pool import (
    ColumnPool,
)


@dataclass(frozen=True, slots=True)
class FakeColumn(Column):
    key: tuple[int, ...]

    def get_key(self) -> Hashable:
        return self.key


def test_every_column_of_the_first_batch_is_fresh() -> None:
    first = FakeColumn(cost=1.0, key=(1,))
    second = FakeColumn(cost=2.0, key=(2,))
    pool = ColumnPool()

    assert pool.add([first, second]) == [first, second]
    assert pool.get_columns() == [first, second]


def test_a_column_with_a_known_key_is_not_fresh_again() -> None:
    pool = ColumnPool()
    pool.add([FakeColumn(cost=1.0, key=(1,))])

    fresh = FakeColumn(cost=3.0, key=(3,))

    assert pool.add([FakeColumn(cost=1.0, key=(1,)), fresh]) == [fresh]


def test_a_batch_of_only_known_columns_adds_nothing() -> None:
    pool = ColumnPool()
    pool.add([FakeColumn(cost=1.0, key=(1,))])

    assert pool.add([FakeColumn(cost=1.0, key=(1,))]) == []
    assert len(pool.get_columns()) == 1


def test_a_duplicate_inside_one_batch_is_added_once() -> None:
    first = FakeColumn(cost=1.0, key=(1,))
    pool = ColumnPool()

    assert pool.add([first, FakeColumn(cost=1.0, key=(1,))]) == [first]

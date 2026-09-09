from template.solvers.column_generation.column import (
    Column,
    build_solution_from_columns,
)
from template.solvers.column_generation.column_pool import ColumnPool


def test_add_returns_only_fresh_columns() -> None:
    pool = ColumnPool()
    first = Column(cost=1.0, item_ids=(0, 1))
    second = Column(cost=1.0, item_ids=(2,))

    assert pool.add([first, second]) == [first, second]
    assert pool.add([first]) == []
    assert pool.get_columns() == [first, second]


def test_columns_with_the_same_items_in_another_order_are_duplicates() -> None:
    pool = ColumnPool()
    pool.add([Column(cost=1.0, item_ids=(0, 1))])

    assert pool.add([Column(cost=5.0, item_ids=(1, 0))]) == []
    assert len(pool.get_columns()) == 1


def test_only_selected_columns_become_assignments() -> None:
    selected = Column(cost=1.0, item_ids=(0, 1))
    solution = build_solution_from_columns(
        {selected: 1.0, Column(cost=1.0, item_ids=(2,)): 0.4}
    )

    assert solution.used_resource_ids == (0,)
    assert solution.assigned_item_ids == (0, 1)

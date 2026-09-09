from collections.abc import Hashable

from template.solvers.branch_and_price_solver.column_generation.column import Column


class ColumnPool:
    """Every column generated anywhere in the tree, deduplicated by key."""

    _columns: list[Column]
    _keys: set[Hashable]

    def __init__(self) -> None:
        self._columns = []
        self._keys = set()

    # Store and return only columns whose key is new; deduplication says nothing
    # about pricing convergence.
    def add(self, columns: list[Column]) -> list[Column]:
        fresh_columns: list[Column] = []
        for column in columns:
            key = column.get_key()
            if key in self._keys:
                continue

            self._keys.add(key)
            self._columns.append(column)
            fresh_columns.append(column)

        return fresh_columns

    def get_columns(self) -> list[Column]:
        return self._columns

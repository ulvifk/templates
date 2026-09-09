from template.solvers.column_generation.column import Column, ColumnKey


class ColumnPool:
    """Deduplicates generated columns; an empty add result is the column generation stop signal."""

    _columns: list[Column]
    _keys: set[ColumnKey]

    def __init__(self) -> None:
        self._columns = []
        self._keys = set()

    def add(self, columns: list[Column]) -> list[Column]:
        """Stores the unseen columns and returns exactly those."""
        fresh = []
        for column in columns:
            if column.key in self._keys:
                continue
            self._keys.add(column.key)
            self._columns.append(column)
            fresh.append(column)
        return fresh

    def get_columns(self) -> list[Column]:
        return self._columns

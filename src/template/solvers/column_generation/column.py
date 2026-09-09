from dataclasses import dataclass

from template.model.solution.assignment import Assignment
from template.model.solution.solution import Solution

# sorted item ids of one column; the pool deduplicates on it
type ColumnKey = tuple[int, ...]


@dataclass(frozen=True, slots=True)
class Column:
    """One resource's item set; the placeholder cost is one because a column occupies one resource."""

    cost: float
    item_ids: tuple[int, ...]

    @property
    def key(self) -> ColumnKey:
        return tuple(sorted(self.item_ids))


def build_solution_from_columns(column_values: dict[Column, float]) -> Solution:
    """The selected columns become assignments; resource ids are handed out in selection order."""
    assignments = []
    for column, value in column_values.items():
        if value <= 0.5:
            continue
        assignments.append(
            Assignment(resource_id=len(assignments), item_ids=column.item_ids)
        )
    return Solution(assignments=tuple(assignments))

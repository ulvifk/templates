from dataclasses import dataclass

from template.model.solution.assignment import Assignment


@dataclass(frozen=True, slots=True)
class Solution:
    assignments: tuple[Assignment, ...]

    @property
    def used_resource_ids(self) -> tuple[int, ...]:
        return tuple(assignment.resource_id for assignment in self.assignments)

    @property
    def assigned_item_ids(self) -> tuple[int, ...]:
        item_ids: list[int] = []
        for assignment in self.assignments:
            item_ids.extend(assignment.item_ids)
        return tuple(item_ids)

from dataclasses import dataclass

from template.model.data.problem_data import ProblemData


@dataclass
class BranchNode:
    """Complete aggregate bounds, so a master can be built without walking back to the parent."""

    # [resource id] -> (lower, upper) in {0, 1}
    resource_use: dict[int, tuple[int, int]]
    # [(resource id, item id)] -> (lower, upper) in {0, 1}
    assignment: dict[tuple[int, int], tuple[int, int]]

    lower_bound: float

    @staticmethod
    def root(problem_data: ProblemData) -> BranchNode:
        return BranchNode(
            resource_use={resource.id: (0, 1) for resource in problem_data.resources},
            assignment={},
            lower_bound=0.0,
        )

    def get_child_with_resource_use(self, resource_id: int, use: int) -> BranchNode:
        child = self._get_copy()
        child.resource_use[resource_id] = (use, use)
        return child

    def get_child_with_assignment(
        self, resource_id: int, item_id: int, value: int
    ) -> BranchNode:
        child = self._get_copy()
        child.assignment[(resource_id, item_id)] = (value, value)
        return child

    def _get_copy(self) -> BranchNode:
        return BranchNode(
            resource_use=dict(self.resource_use),
            assignment=dict(self.assignment),
            lower_bound=self.lower_bound,
        )


def is_pruned_by_incumbent(
    node: BranchNode, incumbent_objective: float, bound_tolerance: float
) -> bool:
    """Whether the node's subtree can no longer beat the incumbent."""
    return node.lower_bound >= incumbent_objective - bound_tolerance

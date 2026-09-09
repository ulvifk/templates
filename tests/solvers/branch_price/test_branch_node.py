from template.model.data.item import Item
from template.model.data.problem_data import ProblemData
from template.model.data.resource import Resource
from template.solvers.branch_price.branch_node import BranchNode, is_pruned_by_incumbent


def build_problem_data() -> ProblemData:
    return ProblemData(
        items=(Item(id=0, weight=3), Item(id=1, weight=4)),
        resources=(Resource(id=0, capacity=5), Resource(id=1, capacity=5)),
    )


def test_root_leaves_every_resource_free() -> None:
    root = BranchNode.root(build_problem_data())

    assert root.resource_use == {0: (0, 1), 1: (0, 1)}
    assert root.assignment == {}
    assert root.lower_bound == 0.0


def test_children_fix_one_bound_and_keep_the_parent_untouched() -> None:
    root = BranchNode.root(build_problem_data())
    root.lower_bound = 2.5

    used = root.get_child_with_resource_use(1, 1)
    assigned = root.get_child_with_assignment(0, 1, 0)

    assert used.resource_use[1] == (1, 1)
    assert assigned.assignment == {(0, 1): (0, 0)}
    assert used.lower_bound == 2.5
    assert root.resource_use[1] == (0, 1)
    assert root.assignment == {}


def test_a_node_is_pruned_only_when_it_cannot_beat_the_incumbent() -> None:
    node = BranchNode.root(build_problem_data())
    node.lower_bound = 3.0

    assert is_pruned_by_incumbent(node, 3.0, 1e-6)
    assert is_pruned_by_incumbent(node, 2.0, 1e-6)
    assert not is_pruned_by_incumbent(node, 4.0, 1e-6)

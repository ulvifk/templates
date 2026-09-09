from template.solvers.branch_price.branch_node import BranchNode
from template.solvers.branch_price.node_selector import NodeSelector


def build_node(lower_bound: float) -> BranchNode:
    return BranchNode(resource_use={}, assignment={}, lower_bound=lower_bound)


def test_the_weakest_bound_is_popped_first() -> None:
    selector = NodeSelector()
    weak = build_node(1.0)
    strong = build_node(4.0)
    middle = build_node(2.0)
    selector.push([strong, weak, middle])

    assert selector.pop() is weak
    assert selector.pop() is middle
    assert selector.pop() is strong


def test_ties_keep_the_insertion_order() -> None:
    selector = NodeSelector()
    first = build_node(1.0)
    second = build_node(1.0)
    selector.push([first, second])

    assert selector.pop() is first
    assert selector.pop() is second


def test_an_empty_selector_has_no_node_and_an_infinite_bound() -> None:
    selector = NodeSelector()

    assert selector.is_empty()
    assert selector.pop() is None
    assert selector.get_open_bound() == float("inf")


def test_the_open_bound_is_the_weakest_open_node() -> None:
    selector = NodeSelector()
    selector.push([build_node(3.0), build_node(1.5)])

    assert not selector.is_empty()
    assert selector.get_open_bound() == 1.5

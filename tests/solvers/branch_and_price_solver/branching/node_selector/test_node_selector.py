import math

from template.solvers.branch_and_price_solver.branching.branch_node import BranchNode
from template.solvers.branch_and_price_solver.branching.node_selector.best_first_node_selector import (
    BestFirstNodeSelector,
)
from template.solvers.branch_and_price_solver.branching.node_selector.depth_first_node_selector import (
    DepthFirstNodeSelector,
)


def test_depth_first_pops_the_first_pushed_child_first() -> None:
    first = BranchNode(
        branching_decisions=(), lower_bound=1.0, master_relaxation_solution={}
    )
    second = BranchNode(
        branching_decisions=(), lower_bound=2.0, master_relaxation_solution={}
    )
    selector = DepthFirstNodeSelector()

    selector.push([first, second])

    assert selector.pop() is first
    assert selector.pop() is second


def test_depth_first_reports_the_smallest_bound_it_holds() -> None:
    selector = DepthFirstNodeSelector()

    selector.push(
        [
            BranchNode(
                branching_decisions=(),
                lower_bound=5.0,
                master_relaxation_solution={},
            ),
            BranchNode(
                branching_decisions=(),
                lower_bound=3.0,
                master_relaxation_solution={},
            ),
        ]
    )

    assert selector.get_best_lower_bound() == 3.0


def test_best_first_pops_the_node_with_the_lowest_bound() -> None:
    worst = BranchNode(
        branching_decisions=(), lower_bound=9.0, master_relaxation_solution={}
    )
    best = BranchNode(
        branching_decisions=(), lower_bound=2.0, master_relaxation_solution={}
    )
    selector = BestFirstNodeSelector()

    selector.push([worst, best])

    assert selector.pop() is best
    assert selector.pop() is worst


def test_best_first_keeps_insertion_order_on_equal_bounds() -> None:
    first = BranchNode(
        branching_decisions=(), lower_bound=4.0, master_relaxation_solution={}
    )
    second = BranchNode(
        branching_decisions=(), lower_bound=4.0, master_relaxation_solution={}
    )
    selector = BestFirstNodeSelector()

    selector.push([first, second])

    assert selector.pop() is first
    assert selector.pop() is second


def test_an_empty_selector_pops_none_and_bounds_nothing() -> None:
    for selector in (DepthFirstNodeSelector(), BestFirstNodeSelector()):
        assert selector.pop() is None
        assert selector.get_best_lower_bound() == math.inf

import math
from dataclasses import dataclass
from unittest.mock import Mock

from template.solvers.branch_and_price_solver.branching.branch_node import (
    BranchNode,
    BranchNodeFactory,
)
from template.solvers.branch_and_price_solver.branching.branching_decision import (
    BranchingDecision,
)
from template.solvers.branch_and_price_solver.branching.branching_rule.branching_rule import (
    BranchingRule,
)
from template.solvers.branch_and_price_solver.column_generation.column import Column


@dataclass(frozen=True, slots=True)
class FakeBranchingDecision(BranchingDecision):
    name: str
    compatible: bool = True

    def is_column_compatible(self, column: Column) -> bool:
        return self.compatible


class FakeBranchingRule(BranchingRule):
    _decisions: tuple[BranchingDecision, ...]

    def __init__(self, decisions: tuple[BranchingDecision, ...]) -> None:
        self._decisions = decisions

    def get_children(self, node: BranchNode) -> list[BranchNode]:
        return [self._build_child(node, decision) for decision in self._decisions]


def test_children_inherit_decisions_and_bound_without_the_parent_solution() -> None:
    root = BranchNodeFactory.build_root()
    assert root.branching_decisions == ()
    assert root.lower_bound == -math.inf
    assert root.master_relaxation_solution == {}

    column = Mock(spec=Column)
    root.lower_bound = 10.0
    root.master_relaxation_solution = {column: 0.5}
    first = FakeBranchingDecision("first")
    second = FakeBranchingDecision("second")
    third = FakeBranchingDecision("third")

    child, sibling = FakeBranchingRule((first, second)).get_children(root)
    (grandchild,) = FakeBranchingRule((third,)).get_children(child)

    assert root.branching_decisions == ()
    assert child.branching_decisions == (first,)
    assert sibling.branching_decisions == (second,)
    assert grandchild.branching_decisions == (first, third)
    assert grandchild.lower_bound == 10.0
    assert child.master_relaxation_solution == {}
    assert sibling.master_relaxation_solution == {}
    assert grandchild.master_relaxation_solution == {}
    assert root.master_relaxation_solution == {column: 0.5}


def test_a_node_accepts_a_column_only_when_every_decision_accepts_it() -> None:
    column = Mock(spec=Column)
    accepted = FakeBranchingDecision("accepted")
    rejected = FakeBranchingDecision("rejected", compatible=False)
    node = BranchNodeFactory.build_root()
    node.branching_decisions = (accepted, rejected)

    assert not node.is_column_compatible(column)

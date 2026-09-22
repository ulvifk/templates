import math
from dataclasses import dataclass
from unittest.mock import Mock, call

from template.solvers.branch_and_price_solver.branching.branch_node import BranchNode
from template.solvers.branch_and_price_solver.branching.branching_decision import (
    BranchingDecision,
)
from template.solvers.branch_and_price_solver.column_generation.column import Column


@dataclass(frozen=True, slots=True)
class FakeBranchingDecision(BranchingDecision):
    """Enforces itself by name on a mock master and a mock pricer."""

    name: str
    compatible: bool = True

    def is_column_compatible(self, column: Column) -> bool:
        return self.compatible

    def apply_to_master(self, master: Mock) -> None:
        master.enforce(self.name)

    def apply_to_pricing(self, pricing_problem: Mock) -> None:
        pricing_problem.enforce(self.name)


def test_a_node_accepts_a_column_only_when_every_decision_accepts_it() -> None:
    column = Mock(spec=Column)
    accepted = FakeBranchingDecision("accepted")
    rejected = FakeBranchingDecision("rejected", compatible=False)
    node = BranchNode(branching_decisions=(accepted, rejected), lower_bound=-math.inf)

    assert not node.is_column_compatible(column)


def test_a_node_enforces_every_decision_on_the_master_in_path_order() -> None:
    master = Mock()
    node = BranchNode(
        branching_decisions=(
            FakeBranchingDecision("first"),
            FakeBranchingDecision("second"),
        ),
        lower_bound=-math.inf,
    )

    node.apply_to_master(master)

    assert master.enforce.call_args_list == [call("first"), call("second")]


def test_a_node_enforces_every_decision_on_the_pricer_in_path_order() -> None:
    pricer = Mock()
    node = BranchNode(
        branching_decisions=(
            FakeBranchingDecision("first"),
            FakeBranchingDecision("second"),
        ),
        lower_bound=-math.inf,
    )

    node.apply_to_pricing(pricer)

    assert pricer.enforce.call_args_list == [call("first"), call("second")]

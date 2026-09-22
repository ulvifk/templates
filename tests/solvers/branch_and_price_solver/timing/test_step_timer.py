from template.solvers.branch_and_price_solver.timing.node_step import NodeStep
from template.solvers.branch_and_price_solver.timing.step_timer import StepTimer
from tests.solvers.branch_and_price_solver.test_branch_and_price_solver import (
    FakeClock,
)


def test_a_step_lasts_since_the_previous_finish_and_repeated_steps_add_up() -> None:
    clock = FakeClock()
    clock.now = 10.0
    step_timer = StepTimer(clock)

    clock.now = 12.0
    step_timer.finish_step(NodeStep.MASTER_SOLVE)
    clock.now = 15.0
    step_timer.finish_step(NodeStep.PRICING)
    clock.now = 16.0
    step_timer.finish_step(NodeStep.MASTER_SOLVE)

    assert step_timer.get_seconds_by_step() == {
        NodeStep.MASTER_SOLVE: 3.0,
        NodeStep.PRICING: 3.0,
    }

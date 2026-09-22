from template.solvers.branch_and_price_solver.timing.clock import Clock
from template.solvers.branch_and_price_solver.timing.node_step import NodeStep


class StepTimer:
    """Splits one node's time into steps; a step lasts since the previous one finished."""

    _clock: Clock
    _last_finished_at: float

    # [step] -> its seconds summed over every finish; absent until it first finishes
    _seconds_by_step: dict[NodeStep, float]

    def __init__(self, clock: Clock) -> None:
        self._clock = clock
        self._last_finished_at = clock.now_seconds()

        self._seconds_by_step = {}

    def finish_step(self, step: NodeStep) -> None:
        finished_at = self._clock.now_seconds()
        seconds = finished_at - self._last_finished_at

        self._seconds_by_step[step] = self._seconds_by_step.get(step, 0.0) + seconds
        self._last_finished_at = finished_at

    def get_seconds_by_step(self) -> dict[NodeStep, float]:
        return self._seconds_by_step

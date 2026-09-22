import time

from template.solvers.branch_and_price_solver.timing.clock import Clock


class SystemClock(Clock):
    def now_seconds(self) -> float:
        return time.perf_counter()

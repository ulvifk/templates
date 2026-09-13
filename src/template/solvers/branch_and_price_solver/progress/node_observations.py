from template.solvers.branch_and_price_solver.progress.node_component import (
    NodeComponent,
)


class NodeObservations:
    """What the timing wrappers measured on the node being explored."""

    # [component] -> its seconds; a component the node never reached is absent
    seconds_by_component: dict[NodeComponent, float]

    compatible_column_count: int
    round_count: int
    new_column_count: int
    child_count: int
    integral: bool | None

    def __init__(self) -> None:
        self.clear()

    def clear(self) -> None:
        self.seconds_by_component = {}

        self.compatible_column_count = 0
        self.round_count = 0
        self.new_column_count = 0
        self.child_count = 0
        self.integral = None

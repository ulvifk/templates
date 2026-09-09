from template.time_space_network.constructor.feasible_arc_calculator import (
    FeasibleArcCalculator,
)
from template.time_space_network.constructor.ts_network_builder import TSNetworkBuilder
from template.time_space_network.data.ts_node.ts_network_node import TSNetworkNode
from template.time_space_network.data.ts_node.ts_node import TSNode


class ForwardExpansion:
    _builder: TSNetworkBuilder
    _calculator: FeasibleArcCalculator

    def __init__(
        self, builder: TSNetworkBuilder, calculator: FeasibleArcCalculator
    ) -> None:
        self._builder = builder
        self._calculator = calculator

    def run(self) -> None:
        pending = self._expand(self._builder.source_node)

        expanded_node_ids: set[int] = set()
        while pending:
            node = pending.pop()
            if node.id in expanded_node_ids:
                continue

            expanded_node_ids.add(node.id)
            pending += self._expand(node)

    def _expand(self, tail_node: TSNode) -> list[TSNetworkNode]:
        heads: list[TSNetworkNode] = []
        for arc in self._calculator.get_feasible_arcs(tail_node):
            self._builder.add_arc(arc)
            if arc.head_node_id == self._builder.sink_node.id:  # the sink never expands
                continue

            heads.append(self._builder.get_node(arc.head_node_id))

        return heads

from abc import ABC, abstractmethod

from template.time_space_network.data.ts_arc.ts_arc import TSArc
from template.time_space_network.data.ts_node.ts_node import TSNode


class FeasibleArcCalculator(ABC):
    # per problem: dispatch on the tail node's type and return every arc that may
    # leave it, creating head nodes through the builder as needed; the sink has none
    @abstractmethod
    def get_feasible_arcs(self, tail_node: TSNode) -> list[TSArc]: ...

    # Example:
    #
    # def get_feasible_arcs(self, tail_node: TSNode) -> list[TSArc]:
    #     if isinstance(tail_node, TSSourceNode):
    #         return self._get_source_arcs()
    #     if isinstance(tail_node, TSDepotNode):
    #         return self._get_movement_arcs(tail_node)
    #     if isinstance(tail_node, TSCustomerNode):
    #         return [
    #             *self._get_movement_arcs(tail_node),
    #             *self._get_service_arcs(tail_node),
    #         ]
    #     return []
    #
    # def _get_ground_arcs(self, node: TSNetworkNode) -> list[TSArc]:
    #     head_minute = node.time_minute + self._config.discretization_minutes
    #     if head_minute > self._horizon_end_minute:
    #         return []
    #
    #     head = self._builder.get_or_create_node(node.location_id, head_minute)
    #     return [GroundArc(self._builder.allocate_arc_id(), node.id, head.id, 0.0)]

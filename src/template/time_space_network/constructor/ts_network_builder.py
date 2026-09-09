from abc import ABC, abstractmethod

from template.time_space_network.constructor.ts_column_builder import TSColumnBuilder
from template.time_space_network.data.ts_arc.ts_arc import TSArc
from template.time_space_network.data.ts_column import TSColumn
from template.time_space_network.data.ts_network import TSNetwork
from template.time_space_network.data.ts_node.ts_network_node import TSNetworkNode
from template.time_space_network.data.ts_node.ts_sink_node import TSSinkNode
from template.time_space_network.data.ts_node.ts_source_node import TSSourceNode


class TSNetworkBuilder(ABC):
    source_node: TSSourceNode
    sink_node: TSSinkNode
    nodes_by_id: dict[int, TSNetworkNode]  # [node_id] -> node
    arcs: dict[int, TSArc]  # [arc_id] -> arc

    _column_builders: dict[int, TSColumnBuilder]  # [location_id] -> column builder
    _next_node_id: int
    _next_arc_id: int

    def __init__(self) -> None:
        self.nodes_by_id = {}
        self.arcs = {}
        self._column_builders = {}
        self._next_node_id = 0
        self._next_arc_id = 0

        self.source_node = TSSourceNode(id=self._allocate_node_id())
        self.sink_node = TSSinkNode(id=self._allocate_node_id())

    def get_or_create_node(self, location_id: int, time_minute: int) -> TSNetworkNode:
        column = self._column_builders.setdefault(
            location_id, TSColumnBuilder(location_id)
        )
        node = column.get_node(time_minute)
        if node is not None:
            return node

        node = self._create_node(self._allocate_node_id(), location_id, time_minute)
        self.nodes_by_id[node.id] = node
        column.add_node(node)

        return node

    def get_node(self, node_id: int) -> TSNetworkNode:
        return self.nodes_by_id[node_id]

    def add_arc(self, arc: TSArc) -> None:
        self.arcs[arc.id] = arc

    def delete_arc(self, arc_id: int) -> None:
        del self.arcs[arc_id]

    def delete_node(self, node_id: int) -> None:
        node = self.nodes_by_id.pop(node_id)
        self._column_builders[node.location_id].remove_node(node.time_minute)

    def allocate_arc_id(self) -> int:
        arc_id = self._next_arc_id
        self._next_arc_id += 1

        return arc_id

    def build(self) -> TSNetwork:
        columns: dict[int, TSColumn] = {}  # [location_id] -> column
        for location_id, column_builder in self._column_builders.items():
            column = column_builder.build()
            if column.nodes:
                columns[location_id] = column

        outgoing_arcs: dict[int, list[TSArc]] = {}  # [tail_node_id] -> arcs
        incoming_arcs: dict[int, list[TSArc]] = {}  # [head_node_id] -> arcs
        for arc in self.arcs.values():
            outgoing_arcs.setdefault(arc.tail_node_id, []).append(arc)
            incoming_arcs.setdefault(arc.head_node_id, []).append(arc)

        return TSNetwork(
            source_node=self.source_node,
            sink_node=self.sink_node,
            columns=columns,
            arcs=self.arcs,
            outgoing_arcs=outgoing_arcs,
            incoming_arcs=incoming_arcs,
        )

    # per problem: return the node subclass for the location's role
    @abstractmethod
    def _create_node(
        self, node_id: int, location_id: int, time_minute: int
    ) -> TSNetworkNode: ...

    # Example:
    #
    # def _create_node(
    #     self, node_id: int, location_id: int, time_minute: int
    # ) -> TSNetworkNode:
    #     location = self._problem_data.locations[location_id]
    #
    #     match location.type:
    #         case LocationType.DEPOT:
    #             return TSDepotNode(node_id, location_id, time_minute)
    #         case LocationType.CUSTOMER:
    #             return TSCustomerNode(
    #                 node_id, location_id, time_minute, location.customer_id
    #             )

    def _allocate_node_id(self) -> int:
        node_id = self._next_node_id
        self._next_node_id += 1

        return node_id

from template.time_space_network.data.ts_column import TSColumn
from template.time_space_network.data.ts_node.ts_network_node import TSNetworkNode


class TSColumnBuilder:
    _location_id: int
    _nodes: dict[int, TSNetworkNode]  # [time] -> node

    def __init__(self, location_id: int) -> None:
        self._location_id = location_id
        self._nodes = {}

    def get_node(self, time_minute: int) -> TSNetworkNode | None:
        return self._nodes.get(time_minute)

    def add_node(self, node: TSNetworkNode) -> None:
        self._nodes[node.time_minute] = node

    def remove_node(self, time_minute: int) -> None:
        del self._nodes[time_minute]

    def build(self) -> TSColumn:
        return TSColumn(
            location_id=self._location_id,
            nodes=dict(sorted(self._nodes.items())),
        )

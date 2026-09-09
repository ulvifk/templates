from dataclasses import dataclass

from template.time_space_network.data.ts_node.ts_network_node import TSNetworkNode


@dataclass(frozen=True, slots=True)
class TSColumn:  # the time axis of one location
    location_id: int
    nodes: dict[int, TSNetworkNode]  # [time] -> node

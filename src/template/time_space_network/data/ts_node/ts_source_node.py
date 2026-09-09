from dataclasses import dataclass

from template.time_space_network.data.ts_node.ts_node import TSNode


@dataclass(frozen=True, slots=True)
class TSSourceNode(TSNode):  # timeless super-source
    pass

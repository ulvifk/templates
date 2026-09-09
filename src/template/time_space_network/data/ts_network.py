from dataclasses import dataclass

from template.time_space_network.data.ts_arc.ts_arc import TSArc
from template.time_space_network.data.ts_column import TSColumn
from template.time_space_network.data.ts_node.ts_sink_node import TSSinkNode
from template.time_space_network.data.ts_node.ts_source_node import TSSourceNode


@dataclass(frozen=True, slots=True)
class TSNetwork:
    source_node: TSSourceNode
    sink_node: TSSinkNode
    columns: dict[int, TSColumn]  # [location_id] -> time axis of that location
    arcs: dict[int, TSArc]  # [arc_id] -> arc
    outgoing_arcs: dict[int, list[TSArc]]  # [tail_node_id] -> arcs
    incoming_arcs: dict[int, list[TSArc]]  # [head_node_id] -> arcs

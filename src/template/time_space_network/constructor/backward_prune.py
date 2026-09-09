from collections import defaultdict

from template.time_space_network.constructor.ts_network_builder import TSNetworkBuilder
from template.time_space_network.data.ts_arc.ts_arc import TSArc


class BackwardPrune:
    """One depth-first pass backward from the sink; whatever it never touches is deleted."""

    _builder: TSNetworkBuilder

    def __init__(self, builder: TSNetworkBuilder) -> None:
        self._builder = builder

    def run(self) -> None:
        visited_arcs = self._traverse_backward_from_sink()
        visited_node_ids = {arc.tail_node_id for arc in visited_arcs}
        visited_arc_ids = {arc.id for arc in visited_arcs}

        self._delete_arcs(visited_arc_ids)
        self._delete_nodes(visited_node_ids)

    def _traverse_backward_from_sink(self) -> list[TSArc]:
        arcs_by_head_node_id = self._get_arcs_by_head_node_id()

        visited_arcs: list[TSArc] = []
        visited_node_ids: set[int] = set()
        stack = [self._builder.sink_node.id]
        while stack:
            node_id = stack.pop()
            for arc in arcs_by_head_node_id[node_id]:
                visited_arcs.append(arc)
                if arc.tail_node_id in visited_node_ids:
                    continue

                visited_node_ids.add(arc.tail_node_id)
                stack.append(arc.tail_node_id)

        return visited_arcs

    def _get_arcs_by_head_node_id(self) -> dict[int, list[TSArc]]:
        arcs_by_head_node_id: dict[int, list[TSArc]] = defaultdict(list)
        for arc in self._builder.arcs.values():
            arcs_by_head_node_id[arc.head_node_id].append(arc)

        return arcs_by_head_node_id

    def _delete_arcs(self, visited_arc_ids: set[int]) -> None:
        for arc_id in list(self._builder.arcs):
            if arc_id not in visited_arc_ids:
                self._builder.delete_arc(arc_id)

    def _delete_nodes(self, visited_node_ids: set[int]) -> None:
        for node_id in list(self._builder.nodes_by_id):
            if node_id not in visited_node_ids:
                self._builder.delete_node(node_id)

from dataclasses import dataclass

from template.time_space_network.constructor.backward_prune import BackwardPrune
from template.time_space_network.constructor.ts_network_builder import TSNetworkBuilder
from template.time_space_network.data.ts_arc.ground_arc import GroundArc
from template.time_space_network.data.ts_node.ts_network_node import TSNetworkNode


@dataclass(frozen=True, slots=True)
class FakeNode(TSNetworkNode):
    pass


class FakeNetworkBuilder(TSNetworkBuilder):
    def _create_node(
        self, node_id: int, location_id: int, time_minute: int
    ) -> TSNetworkNode:
        return FakeNode(id=node_id, location_id=location_id, time_minute=time_minute)


def build_network_with_one_dead_end() -> TSNetworkBuilder:
    # source -> a -> b -> sink, plus the dead end a -> c
    builder = FakeNetworkBuilder()
    a = builder.get_or_create_node(location_id=1, time_minute=0)
    b = builder.get_or_create_node(location_id=2, time_minute=1)
    c = builder.get_or_create_node(location_id=3, time_minute=1)

    builder.add_arc(GroundArc(0, builder.source_node.id, a.id, 0.0))
    builder.add_arc(GroundArc(1, a.id, b.id, 0.0))
    builder.add_arc(GroundArc(2, b.id, builder.sink_node.id, 0.0))
    builder.add_arc(GroundArc(3, a.id, c.id, 0.0))

    return builder


def test_prune_deletes_the_node_that_cannot_reach_the_sink() -> None:
    builder = build_network_with_one_dead_end()
    dead_end = builder.get_or_create_node(location_id=3, time_minute=1)

    BackwardPrune(builder).run()

    assert dead_end.id not in builder.nodes_by_id


def test_prune_deletes_the_arc_into_the_dead_end() -> None:
    builder = build_network_with_one_dead_end()

    BackwardPrune(builder).run()

    assert set(builder.arcs) == {0, 1, 2}


def test_prune_keeps_every_node_on_a_path_to_the_sink() -> None:
    builder = build_network_with_one_dead_end()
    a = builder.get_or_create_node(location_id=1, time_minute=0)
    b = builder.get_or_create_node(location_id=2, time_minute=1)

    BackwardPrune(builder).run()

    assert set(builder.nodes_by_id) == {a.id, b.id}

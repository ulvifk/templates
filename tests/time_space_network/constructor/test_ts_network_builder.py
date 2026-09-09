from dataclasses import dataclass

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


def test_get_or_create_node_returns_the_same_node_for_the_same_location_and_time() -> (
    None
):
    builder = FakeNetworkBuilder()

    first = builder.get_or_create_node(location_id=1, time_minute=30)
    second = builder.get_or_create_node(location_id=1, time_minute=30)

    assert first is second


def test_get_or_create_node_gives_different_ids_to_different_locations_and_times() -> (
    None
):
    builder = FakeNetworkBuilder()

    same_location_later = builder.get_or_create_node(location_id=1, time_minute=30)
    other_location = builder.get_or_create_node(location_id=2, time_minute=30)
    other_time = builder.get_or_create_node(location_id=1, time_minute=60)

    node_ids = {same_location_later.id, other_location.id, other_time.id}
    assert len(node_ids) == 3


def test_build_sorts_the_nodes_of_each_column_by_time() -> None:
    builder = FakeNetworkBuilder()
    builder.get_or_create_node(location_id=1, time_minute=20)
    builder.get_or_create_node(location_id=1, time_minute=0)
    builder.get_or_create_node(location_id=1, time_minute=10)

    network = builder.build()

    assert list(network.columns[1].nodes) == [0, 10, 20]


def test_build_drops_a_column_whose_nodes_were_all_deleted() -> None:
    builder = FakeNetworkBuilder()
    builder.get_or_create_node(location_id=1, time_minute=0)
    deleted = builder.get_or_create_node(location_id=2, time_minute=0)

    builder.delete_node(deleted.id)
    network = builder.build()

    assert set(network.columns) == {1}


def test_build_indexes_arcs_by_their_tail_and_head_nodes() -> None:
    builder = FakeNetworkBuilder()
    first = builder.get_or_create_node(location_id=1, time_minute=0)
    second = builder.get_or_create_node(location_id=1, time_minute=10)
    entering = GroundArc(
        builder.allocate_arc_id(), builder.source_node.id, first.id, 0.0
    )
    ground = GroundArc(builder.allocate_arc_id(), first.id, second.id, 0.0)

    builder.add_arc(entering)
    builder.add_arc(ground)
    network = builder.build()

    assert network.outgoing_arcs[builder.source_node.id] == [entering]
    assert network.outgoing_arcs[first.id] == [ground]
    assert network.incoming_arcs[first.id] == [entering]
    assert network.incoming_arcs[second.id] == [ground]

from dataclasses import dataclass

from template.time_space_network.constructor.feasible_arc_calculator import (
    FeasibleArcCalculator,
)
from template.time_space_network.constructor.forward_expansion import ForwardExpansion
from template.time_space_network.constructor.ts_network_builder import TSNetworkBuilder
from template.time_space_network.data.ts_arc.ground_arc import GroundArc
from template.time_space_network.data.ts_arc.ts_arc import TSArc
from template.time_space_network.data.ts_node.ts_network_node import TSNetworkNode
from template.time_space_network.data.ts_node.ts_node import TSNode


@dataclass(frozen=True, slots=True)
class FakeNode(TSNetworkNode):
    pass


class FakeNetworkBuilder(TSNetworkBuilder):
    def _create_node(
        self, node_id: int, location_id: int, time_minute: int
    ) -> TSNetworkNode:
        return FakeNode(id=node_id, location_id=location_id, time_minute=time_minute)


class FakeFeasibleArcCalculator(FeasibleArcCalculator):
    _builder: TSNetworkBuilder
    # [tail_node_id] -> head (location_id, time_minute), None for the sink
    _script: dict[int, list[tuple[int, int] | None]]

    def __init__(
        self,
        builder: TSNetworkBuilder,
        script: dict[int, list[tuple[int, int] | None]],
    ) -> None:
        self._builder = builder
        self._script = script

    def get_feasible_arcs(self, tail_node: TSNode) -> list[TSArc]:
        arcs: list[TSArc] = []
        for head in self._script[tail_node.id]:
            arcs.append(self._build_arc(tail_node.id, head))

        return arcs

    def _build_arc(self, tail_node_id: int, head: tuple[int, int] | None) -> TSArc:
        if head is None:
            return GroundArc(
                self._builder.allocate_arc_id(),
                tail_node_id,
                self._builder.sink_node.id,
                0.0,
            )

        head_node = self._builder.get_or_create_node(head[0], head[1])

        return GroundArc(
            self._builder.allocate_arc_id(), tail_node_id, head_node.id, 0.0
        )


def run_expansion_over_a_diamond() -> TSNetworkBuilder:
    # source -> (10, 0) and (20, 0), both -> the shared head (30, 5), which -> sink
    builder = FakeNetworkBuilder()
    script: dict[int, list[tuple[int, int] | None]] = {
        builder.source_node.id: [(10, 0), (20, 0)],
        2: [(30, 5)],
        3: [(30, 5)],
        4: [None],
    }

    ForwardExpansion(builder, FakeFeasibleArcCalculator(builder, script)).run()

    return builder


def test_expansion_creates_one_node_per_scripted_location_and_time() -> None:
    builder = run_expansion_over_a_diamond()

    assert set(builder.nodes_by_id) == {2, 3, 4}


def test_expansion_adds_every_scripted_arc_exactly_once() -> None:
    builder = run_expansion_over_a_diamond()

    endpoints = [(arc.tail_node_id, arc.head_node_id) for arc in builder.arcs.values()]
    assert sorted(endpoints) == [(0, 2), (0, 3), (2, 4), (3, 4), (4, 1)]

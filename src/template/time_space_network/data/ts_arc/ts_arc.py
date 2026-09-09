from abc import ABC
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TSArc(ABC):
    id: int
    tail_node_id: int  # source_node.id for arcs leaving the source
    head_node_id: int  # sink_node.id for arcs entering the sink
    cost: float

    # per problem: one subclass per arc type (travel, service, hold, ...); the
    # subclass is the arc's type, so constraints select arcs by isinstance

    # Example:
    #
    # @dataclass(frozen=True, slots=True)
    # class TravelArc(TSArc):
    #     pass

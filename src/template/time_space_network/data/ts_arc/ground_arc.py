from dataclasses import dataclass

from template.time_space_network.data.ts_arc.ts_arc import TSArc


@dataclass(frozen=True, slots=True)
class GroundArc(TSArc):  # (i, t) -> (i, t + delta)
    pass

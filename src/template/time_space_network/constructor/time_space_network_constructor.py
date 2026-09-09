from template.time_space_network.constructor.backward_prune import BackwardPrune
from template.time_space_network.constructor.feasible_arc_calculator import (
    FeasibleArcCalculator,
)
from template.time_space_network.constructor.forward_expansion import ForwardExpansion
from template.time_space_network.constructor.ts_network_builder import TSNetworkBuilder
from template.time_space_network.data.ts_network import TSNetwork


class TimeSpaceNetworkConstructor:
    _builder: TSNetworkBuilder
    _forward_expansion: ForwardExpansion
    _backward_prune: BackwardPrune

    def __init__(
        self, builder: TSNetworkBuilder, calculator: FeasibleArcCalculator
    ) -> None:
        self._builder = builder

        self._forward_expansion = ForwardExpansion(builder, calculator)
        self._backward_prune = BackwardPrune(builder)

    def construct(self) -> TSNetwork:
        self._forward_expansion.run()
        self._backward_prune.run()

        return self._builder.build()

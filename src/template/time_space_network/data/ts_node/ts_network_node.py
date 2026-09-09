from abc import ABC
from dataclasses import dataclass

from template.time_space_network.data.ts_node.ts_node import TSNode


@dataclass(frozen=True, slots=True)
class TSNetworkNode(TSNode, ABC):  # n = (i, t)
    location_id: int  # i; the time axis this node lies on
    time_minute: int  # t

    # per problem: one subclass per location role (depot, customer, break, ...),
    # carrying the ids that role needs

    # Example:
    #
    # @dataclass(frozen=True, slots=True)
    # class TSCustomerNode(TSNetworkNode):
    #     customer_id: int

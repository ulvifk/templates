from abc import ABC, abstractmethod
from collections.abc import Hashable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Column(ABC):
    cost: float

    # per problem: a subclass adds what the column covers; get_key identifies it for
    # deduplication in the pool. Equal keys imply equal costs and row coefficients
    # at every node.
    @abstractmethod
    def get_key(self) -> Hashable: ...

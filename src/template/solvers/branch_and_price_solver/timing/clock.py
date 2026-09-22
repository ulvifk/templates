from abc import ABC, abstractmethod


class Clock(ABC):
    # seconds on a monotonic scale; only differences between readings mean anything
    @abstractmethod
    def now_seconds(self) -> float: ...

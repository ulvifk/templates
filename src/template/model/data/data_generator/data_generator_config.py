from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DataGeneratorConfig:
    num_items: int
    num_resources: int
    capacity: int
    max_weight: int
    seed: int

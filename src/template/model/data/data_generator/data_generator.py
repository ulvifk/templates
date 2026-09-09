from random import Random

from template.model.data.data_generator.data_generator_config import (
    DataGeneratorConfig,
)
from template.model.data.item import Item
from template.model.data.problem_data import ProblemData
from template.model.data.resource import Resource


class DataGenerator:
    config: DataGeneratorConfig
    random: Random

    def __init__(self, config: DataGeneratorConfig) -> None:
        self.config = config
        self.random = Random(config.seed)

    def generate(self) -> ProblemData:
        items = self._build_items()
        resources = self._build_resources()
        return ProblemData(items=items, resources=resources)

    def _build_items(self) -> tuple[Item, ...]:
        items: list[Item] = []
        for item_id in range(self.config.num_items):
            weight = self.random.randint(1, self.config.max_weight)
            items.append(Item(id=item_id, weight=weight))
        return tuple(items)

    def _build_resources(self) -> tuple[Resource, ...]:
        resources: list[Resource] = []
        for resource_id in range(self.config.num_resources):
            resources.append(Resource(id=resource_id, capacity=self.config.capacity))
        return tuple(resources)

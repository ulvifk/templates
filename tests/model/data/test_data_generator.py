from template.model.data.data_generator.data_generator import DataGenerator
from template.model.data.data_generator.data_generator_config import (
    DataGeneratorConfig,
)


def build_config(seed: int) -> DataGeneratorConfig:
    return DataGeneratorConfig(
        num_items=10,
        num_resources=4,
        capacity=20,
        max_weight=8,
        seed=seed,
    )


def test_same_seed_generates_equal_instances() -> None:
    first = DataGenerator(build_config(0)).generate()
    second = DataGenerator(build_config(0)).generate()
    assert first == second


def test_different_seeds_generate_different_weights() -> None:
    first = DataGenerator(build_config(0)).generate()
    second = DataGenerator(build_config(1)).generate()
    assert first.items != second.items


def test_generated_weights_stay_within_bounds() -> None:
    problem_data = DataGenerator(build_config(0)).generate()
    for item in problem_data.items:
        assert 1 <= item.weight <= 8

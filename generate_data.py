import logging
import sys
from math import ceil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from template.model.data.data_generator.data_generator import DataGenerator
from template.model.data.data_generator.data_generator_config import (
    DataGeneratorConfig,
)
from template.model.data.problem_data_parser import ProblemDataParser
from template.validation.validation import Validation

SIZES = {"S": 10, "M": 20}
TIGHTNESS = {"T": 0.9, "L": 0.6}
SEEDS = [0, 1, 2]

CAPACITY = 40
MAX_WEIGHT = 10

OUTPUT_DIR = Path(__file__).resolve().parent / "instances"


def build_config(num_items: int, tightness: float, seed: int) -> DataGeneratorConfig:
    num_resources = ceil(num_items * MAX_WEIGHT / (tightness * CAPACITY))
    return DataGeneratorConfig(
        num_items=num_items,
        num_resources=num_resources,
        capacity=CAPACITY,
        max_weight=MAX_WEIGHT,
        seed=seed,
    )


def write_instance(size: str, tightness: str, seed: int) -> str:
    config = build_config(SIZES[size], TIGHTNESS[tightness], seed)
    problem_data = DataGenerator(config).generate()
    Validation.validate(problem_data)

    name = f"{size}_{tightness}_s{seed}.json"
    (OUTPUT_DIR / name).write_text(ProblemDataParser.to_json(problem_data))
    logging.info(
        "wrote %s (%d items, %d resources)",
        name,
        len(problem_data.items),
        len(problem_data.resources),
    )
    return name


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s", force=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    written_names: set[str] = set()
    for size in SIZES:
        for tightness in TIGHTNESS:
            for seed in SEEDS:
                written_names.add(write_instance(size, tightness, seed))

    for path in OUTPUT_DIR.glob("*.json"):
        if path.name not in written_names:
            path.unlink()


if __name__ == "__main__":
    main()

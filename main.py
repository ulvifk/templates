import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from template.model.data.data_generator.data_generator import DataGenerator
from template.model.data.data_generator.data_generator_config import (
    DataGeneratorConfig,
)
from template.model.data.problem_data import ProblemData
from template.model.solve_result import SolveResult
from template.solvers.mip_solver.mip_config import MIPConfig
from template.solvers.mip_solver.mip_solver import MIPSolver

NUM_ITEMS = 20
NUM_RESOURCES = 8
CAPACITY = 40
MAX_WEIGHT = 10
SEED = 0

TIME_LIMIT_SECONDS = 300.0


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s", force=True)


def generate_data() -> ProblemData:
    config = DataGeneratorConfig(
        num_items=NUM_ITEMS,
        num_resources=NUM_RESOURCES,
        capacity=CAPACITY,
        max_weight=MAX_WEIGHT,
        seed=SEED,
    )
    generator = DataGenerator(config)
    return generator.generate()


def solve_mip(problem_data: ProblemData) -> SolveResult:
    config = MIPConfig(time_limit_seconds=TIME_LIMIT_SECONDS)
    solver = MIPSolver(config)
    return solver.solve(problem_data)


def main() -> None:
    configure_logging()

    problem_data = generate_data()
    result = solve_mip(problem_data)

    logging.info(
        "status=%s objective=%s bound=%s runtime=%.2fs",
        result.status.value,
        result.objective_value,
        result.best_bound,
        result.runtime_seconds,
    )


if __name__ == "__main__":
    main()

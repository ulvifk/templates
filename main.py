import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from template.feasibility.feasibility_validation import FeasibilityValidation
from template.logging_config import LogLevel, configure_logging
from template.model.data.problem_data_parser import ProblemDataParser
from template.solvers.solver import Solver
from template.validation.validation import Validation

INSTANCE_PATH = Path(__file__).resolve().parent / "instances" / "example.json"
LOG_LEVEL = LogLevel.INFO


def build_solver() -> Solver:
    raise NotImplementedError("Return the solver for this run with its config.")


def main() -> None:
    configure_logging(LOG_LEVEL)

    problem_data = ProblemDataParser.from_json(INSTANCE_PATH.read_text())
    Validation.validate(problem_data)

    result = build_solver().solve(problem_data)
    if result.solution is not None:
        FeasibilityValidation.validate(result.solution, problem_data)

    logging.info("%s", result.meta_data)


if __name__ == "__main__":
    main()

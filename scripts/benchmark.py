import csv
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from template.feasibility.feasibility_validation import (  # noqa: E402
    FeasibilityValidation,
)
from template.model.data.problem_data_parser import ProblemDataParser  # noqa: E402
from template.model.solve_status import SolveStatus  # noqa: E402
from template.solvers.mip_solver.mip_config import MIPConfig  # noqa: E402
from template.solvers.mip_solver.mip_solver import MIPSolver  # noqa: E402
from template.validation.validation import Validation  # noqa: E402

INSTANCE_PATHS = sorted((ROOT / "instances").glob("*.json"))
TIME_LIMIT_SECONDS = 3600.0

RESULTS_PATH = ROOT / "artifacts" / "benchmark_results.csv"
FIELDNAMES = [
    "instance",
    "solver",
    "status",
    "runtime_seconds",
    "objective_value",
    "best_bound",
    "absolute_gap",
    "used_resources",
]


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s", force=True)
    solver = MIPSolver(MIPConfig(time_limit_seconds=TIME_LIMIT_SECONDS))

    with RESULTS_PATH.open("w", newline="") as results_file:
        writer = csv.DictWriter(results_file, fieldnames=FIELDNAMES)
        writer.writeheader()

        for instance_path in INSTANCE_PATHS:
            problem_data = ProblemDataParser.from_json(instance_path.read_text())
            Validation.validate(problem_data)

            result = solver.solve(problem_data)

            if result.status is SolveStatus.NO_INCUMBENT:
                writer.writerow(
                    {
                        "instance": instance_path.stem,
                        "solver": result.solver_name,
                        "status": result.status.value,
                        "runtime_seconds": result.runtime_seconds,
                        "best_bound": result.best_bound,
                    }
                )
                results_file.flush()
                print(
                    f"{instance_path.stem}: status={result.status.value}, "
                    f"runtime={result.runtime_seconds:.2f}s, "
                    f"bound={result.best_bound}"
                )
                continue

            FeasibilityValidation.validate(result.solution, problem_data)
            absolute_gap = result.objective_value - result.best_bound

            writer.writerow(
                {
                    "instance": instance_path.stem,
                    "solver": result.solver_name,
                    "status": result.status.value,
                    "runtime_seconds": result.runtime_seconds,
                    "objective_value": result.objective_value,
                    "best_bound": result.best_bound,
                    "absolute_gap": absolute_gap,
                    "used_resources": len(result.solution.used_resource_ids),
                }
            )
            results_file.flush()
            print(
                f"{instance_path.stem}: status={result.status.value}, "
                f"runtime={result.runtime_seconds:.2f}s, "
                f"objective={result.objective_value}, "
                f"bound={result.best_bound}, gap={absolute_gap}"
            )


if __name__ == "__main__":
    main()

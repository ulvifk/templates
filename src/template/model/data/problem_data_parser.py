import json
from dataclasses import asdict

from template.model.data.problem_data import ProblemData


class ProblemDataParser:
    @staticmethod
    def from_json(text: str) -> ProblemData:
        raise NotImplementedError("Rebuild every entity tuple from the parsed dict.")

    @staticmethod
    def to_json(problem_data: ProblemData) -> str:
        return json.dumps(asdict(problem_data), indent=4)

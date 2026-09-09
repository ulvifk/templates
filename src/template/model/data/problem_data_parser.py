import json
from dataclasses import asdict

from template.model.data.item import Item
from template.model.data.problem_data import ProblemData
from template.model.data.resource import Resource


class ProblemDataParser:
    @staticmethod
    def from_json(text: str) -> ProblemData:
        parsed = json.loads(text)
        items = tuple(Item(**item) for item in parsed["items"])
        resources = tuple(Resource(**resource) for resource in parsed["resources"])
        return ProblemData(items=items, resources=resources)

    @staticmethod
    def to_json(problem_data: ProblemData) -> str:
        return json.dumps(asdict(problem_data), indent=4)

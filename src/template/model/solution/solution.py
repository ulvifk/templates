from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Solution:
    # per problem: the decisions a solver returns
    pass


class SolutionFactory:
    @staticmethod
    def build_empty() -> Solution:
        raise NotImplementedError("Return a Solution whose every collection is empty.")

from template.model.solution.solution import Solution


class SolutionFactory:
    @staticmethod
    def build_empty() -> Solution:
        raise NotImplementedError("Return a Solution whose every collection is empty.")

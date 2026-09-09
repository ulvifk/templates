from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Duals:
    # per problem: [row key] -> dual of that master row
    pass

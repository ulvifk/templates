from dataclasses import dataclass

# Costs count resources, so the entry test is absolute rather than relative.
REDUCED_COST_TOLERANCE = 1e-7


@dataclass(frozen=True, slots=True)
class Duals:
    # [item id] -> dual of the item's covering row
    items: dict[int, float]


def has_negative_reduced_cost(column_cost: float, reward: float) -> bool:
    """Whether a priced column is worth adding to the master."""
    return column_cost - reward < -REDUCED_COST_TOLERANCE

from template.time_space_network.constructor.discretization import (
    ceil_to_step,
    floor_to_step,
)


def test_a_float_sum_on_a_grid_minute_ceils_to_that_minute() -> None:
    arrival_minute = 0.1 * 3 * 100  # 30.000000000000004

    assert ceil_to_step(arrival_minute, 15) == 30


def test_a_minute_just_below_a_grid_minute_floors_to_that_minute() -> None:
    assert floor_to_step(29.999999999999996, 15) == 30


def test_minutes_between_grid_minutes_round_to_the_next_or_previous_step() -> None:
    assert ceil_to_step(31.0, 15) == 45
    assert floor_to_step(31.0, 15) == 30

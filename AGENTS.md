# AGENTS.md

This repository holds code skeletons that define how the user structures optimization-research projects. When asked to initialize a new project from a template, copy the layout and abstractions, rename `template` to the project package, replace the placeholder domain (items/resources) with the real one, and keep every convention below.

## Commands

uv sync
uv run ruff check .
uv run ruff format .
uv run pyrefly check
uv run pytest

Run all four checks after every change.

## Layout

- `src/<package>/model/data`: input entities (frozen dataclasses), `ProblemData`, parser, generator.
- `src/<package>/model/solution`: solution value objects. `model/solve_result.py` wraps data + solution + status.
- `src/<package>/solvers/<family>_solver` or `solvers/<technique>`: one package per algorithm, each with its own config dataclass and `SOLVER_NAME`.
- `src/<package>/validation`: input-data rules. `src/<package>/feasibility`: solution checks. Both use one class per rule plus a facade with a `ClassVar` registry.
- `instances/`: generated JSON instances named by design point and seed. `artifacts/`: script outputs. `scripts/`: benchmarks.
- `tests/` mirrors `src/<package>/`.
- Entry scripts (`main.py`, `generate_data.py`, `scripts/*.py`) use UPPER_CASE module constants, never CLI arguments.

## Code style

- Ruff (88, double quotes) and Pyrefly. Declare every class variable and instance variable under the class, grouped by purpose with one blank line between groups.
- Frozen, slotted dataclasses for all data; tuples for collections; ids are ints; units in field names.
- Prefer idiomatic Python over abstraction. Classes only for real domain state or lifecycle.
- No defensive checks, fallbacks, try/except, or defensive copies. Let wrong input fail.
- Early returns. A multi-clause condition becomes a named predicate with one clause per return.
- No default parameter values. Empty `__init__.py`. One class per file, file named after the class.
- Helpers return new values; the caller mutates. Group statements in a method by phase, one blank line between phases.
- Names carry plain domain meaning, not technique jargon. Docstrings are one line at most and only when the name is not enough. Indexed structures get a `[key] -> value` comment.
- Delete what a change makes redundant in the same change.

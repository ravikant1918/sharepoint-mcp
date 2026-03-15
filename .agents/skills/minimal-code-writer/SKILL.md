# Minimal Code Writer — 'Do Not Copy' Minimal Implementation Skill

Purpose

- Produce small, original, well-structured code that implements required behavior without copying large blocks from external sources.
- Enforce a minimal, standard project layout and coding guidelines so new code is easy to review and integrate.

When to use

- When asked to implement a new feature, helper, tool, or to refactor a small module.
- When asked to scaffold a minimal runnable example (CLI, microservice handler, library module).

Principles

1. Do not copy-paste large external code. It's acceptable to read documentation and translate ideas into original code.
2. Keep changes minimal and focused: change only what's necessary to implement the feature or fix the bug.
3. Prefer clarity over cleverness. Use descriptive names and small functions.
4. Make code testable: inject dependencies, avoid hidden global state, and keep I/O at the edges.
5. Follow repository style and existing patterns whenever reasonable.

Standard directory layout (Python)

```
src/<package>/
  __init__.py
  module.py
  helpers/
    __init__.py
    utils.py
tests/
  conftest.py
  test_module.py
pyproject.toml
README.md
```

Implementation approach

- Start with a one-paragraph plan: responsibilities, inputs, outputs, edge cases.
- Create the minimal module implementing clean public functions / classes with docstrings.
- Add small unit tests exercising the behavior (happy path + 1-2 edge cases).
- Avoid adding heavy dependencies; prefer stdlib unless justified.

Testing & validation

- Provide tests under `tests/` that run with `pytest`.
- Mock external calls where needed; keep tests isolated and fast.

Documentation

- Add a short README or module docstring describing usage and exported symbols.

Code style & safety

- Type hints for public functions.
- Short functions (ideally <40 LOC).
- No inline credential or secrets handling; read from environment via a Settings object.

Example deliverable when asked for minimal feature

- New file: `src/<package>/feature.py` with 40–120 lines implementing behavior.
- Tests: `tests/test_feature.py` with 3–6 focused tests.
- Update `tests/conftest.py` only if a reusable fixture is required.
- Short run instructions in a README bullet.

License / attribution

- If referencing a public algorithm, include a one-line attribution comment and prefer to reimplement in own words rather than copy.

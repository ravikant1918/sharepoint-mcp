# Contributing

Contributions are welcome! Please follow the steps below to keep the codebase clean and consistent.

## Development Setup

```bash
git clone https://github.com/ravikant1918/mcp-sharepoint.git
cd mcp-sharepoint

python -m venv .venv
source .venv/bin/activate

make install-dev     # installs package + pytest extras
cp .env.example .env # fill in your SharePoint credentials
```

## Project Layout

See [architecture.md](architecture.md) for a full breakdown.

```
services/    ← Business logic — add new SharePoint operations here
tools/       ← MCP tool registration — add new @mcp.tool() wrappers here
utils/       ← Pure utility functions (parsers, helpers)
tests/       ← Unit tests — one file per service/util module
```

## Making Changes

### Adding a New Tool

1. Add the business logic function to the relevant file in `services/`
2. Register it in the corresponding file in `tools/` using `@mcp.tool()`
3. Export it from `services/__init__.py`
4. Write a unit test in `tests/`

### Adding a New Parser

1. Add a `parse_xxx(bytes) -> Tuple[str, metadata]` function in `utils/parsers.py`
2. Add the extension mapping to `_FILE_TYPE_MAP`
3. Handle the new type in `services/document_service.get_document_content()`
4. Add parametrised cases to `tests/test_parsers.py`

## Running Tests

```bash
make test
# or
.venv/bin/python -m pytest tests/ -v
```

All tests must pass before submitting a PR. Tests must **not** require real SharePoint credentials — mock everything using `unittest.mock.patch`.

## Code Style

- Follow **PEP 8**
- Use **type hints** on all public function signatures
- Use `logging.getLogger(__name__)` in every module — no `print()` statements
- Keep the `tools/` layer free of business logic

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(tools): add Copy_Document tool
fix(services): handle missing file gracefully in delete_document
docs: update tools-reference with new parameters
refactor(parsers): lazy-import pandas in parse_excel
```

## Submitting a Pull Request

1. Fork the repository on GitHub
2. Create a feature branch: `git checkout -b feat/my-new-tool`
3. Make your changes and add tests
4. Run `make test` — all tests must pass
5. Open a Pull Request against `main`

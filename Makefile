.PHONY: install install-dev run inspect test lint clean

## Install the package in editable mode
install:
	pip install -e .

## Install with development extras (pytest, etc.)
install-dev:
	pip install -e ".[dev]"

## Run the MCP server directly (requires .env to be configured)
run:
	python -m mcp_sharepoint

## Launch MCP Inspector UI for interactive testing
inspect:
	npx -y @modelcontextprotocol/inspector -- python -m mcp_sharepoint

## Run all unit tests
test:
	python -m pytest tests/ -v

## Quick import / syntax check (no SharePoint credentials needed)
check:
	python -c "from mcp_sharepoint.exceptions import SharePointConfigError; print('exceptions ✓')"
	python -c "from mcp_sharepoint.utils.parsers import detect_file_type; print('parsers ✓', detect_file_type('test.pdf'))"

## Remove Python cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	rm -f mcp_sharepoint.log

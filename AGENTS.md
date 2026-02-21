# AGENTS.md

Guidelines for AI agents working on mdtopdf.

## Development Commands

```bash
# Install dependencies
uv sync

# Install Playwright chromium
uv run --no-sync python -m playwright install chromium

# Run tests
uv run pytest tests/ -v

# Run CLI
uv run mdtopdf input.md
```

## Code Style

- Use `re` module for HTML parsing (not simple string operations)
- Use `frozen=True` dataclass for configuration objects
- Always close browser in `finally` block
- Reuse browser instance for batch conversions

## Testing

- Unit tests go in `tests/test_convert.py`
- Test functions that don't require pandoc/Playwright (e.g., `_insert_base_href`, `_inject_style_tag`)
- Include local copies of functions in test file to avoid import errors

## Adding New Options

When adding new CLI options:
1. Add argument to `cli.py` → `_build_parser()`
2. Pass to `convert_markdown_files()` in `cli.py`
3. Add parameter to `convert_markdown_files()` in `convert.py`
4. Add field to `ConvertOptions` dataclass (use `tuple` for lists)
5. Use the option in relevant functions
6. Update README.md Options section

## Common Issues

- `ModuleNotFoundError: No module named 'playwright'` → Run `uv sync`
- `Executable doesn't exist` → Run `python -m playwright install chromium`
- Test import errors → Include function definitions locally in test file

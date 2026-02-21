# mdtopdf

Markdown → HTML → PDF converter using pandoc and Playwright.

## Project Structure

```
mdtopdf/
├── src/mdtopdf/
│   ├── __init__.py
│   ├── cli.py          # CLI argument parser and main entry point
│   ├── convert.py      # Core conversion logic
│   └── assets/
│       └── default.css # Default stylesheet
├── tests/
│   ├── __init__.py
│   └── test_convert.py # Unit tests for HTML manipulation functions
├── pyproject.toml      # Project configuration
├── README.md           # User documentation
└── uv.lock
```

## Key Technologies

- **pandoc**: Markdown to HTML conversion
- **Playwright**: HTML to PDF generation (Chromium only)
- **uv**: Package manager (recommended)
- **Python 3.13+**

## Important Notes

- Browser (Chromium) is reused across batch conversions for performance
- Default CSS includes Japanese font stack: Noto Sans JP, Hiragino, Yu Gothic, Meiryo
- pandoc version is checked to determine `--embed-resources` vs `--self-contained` fallback

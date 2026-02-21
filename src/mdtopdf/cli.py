from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mdtopdf.convert import convert_markdown_files


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mdtopdf", description="Markdown → HTML → PDF (pandoc + Playwright)"
    )
    parser.add_argument("inputs", nargs="+", help="Input Markdown files (*.md)")
    parser.add_argument("-o", "--output", help="Output PDF path (single input only)")
    parser.add_argument("--outdir", help="Output directory (multiple inputs)")
    parser.add_argument(
        "--css",
        action="append",
        default=[],
        help="Extra CSS file path (can be repeated)",
    )
    parser.add_argument(
        "--no-default-css", action="store_true", help="Disable built-in default CSS"
    )
    parser.add_argument("--paper", default="A4", help="Paper size (e.g. A4, Letter)")
    parser.add_argument("--margin", default="20mm", help="Page margin (e.g. 20mm, 1in)")
    parser.add_argument(
        "--table-font-size", default="10pt", help="Table font size (e.g. 10pt)"
    )
    parser.add_argument(
        "--font-family",
        default="Noto Sans JP, Hiragino Kaku Gothic ProN, Yu Gothic, Meiryo, sans-serif",
        help="Font family for body text",
    )
    parser.add_argument(
        "--browser",
        default="chromium",
        choices=["chromium", "firefox", "webkit"],
        help="Browser to use for PDF generation (default: chromium)",
    )
    parser.add_argument("--timeout", type=int, default=30000, help="Timeout in ms")

    embed = parser.add_mutually_exclusive_group()
    embed.add_argument(
        "--embed-resources", dest="embed_resources", action="store_true", default=True
    )
    embed.add_argument(
        "--no-embed-resources", dest="embed_resources", action="store_false"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    input_paths = [Path(p) for p in args.inputs]
    for p in input_paths:
        if not p.exists():
            parser.error(f"Input not found: {p}")
        if p.is_dir():
            parser.error(f"Input is a directory: {p}")

    if args.output and len(input_paths) != 1:
        parser.error("--output is only allowed with a single input")
    if args.output and args.outdir:
        parser.error("Use either --output or --outdir, not both")

    output_path = Path(args.output) if args.output else None
    outdir = Path(args.outdir) if args.outdir else None
    css_paths = [Path(p) for p in args.css]

    for p in css_paths:
        if not p.exists():
            parser.error(f"CSS file not found: {p}")

    ok = convert_markdown_files(
        input_paths,
        output_path=output_path,
        outdir=outdir,
        css_paths=css_paths,
        use_default_css=not args.no_default_css,
        paper=args.paper,
        margin=args.margin,
        table_font_size=args.table_font_size,
        font_family=args.font_family,
        browser=args.browser,
        timeout_ms=args.timeout,
        embed_resources=args.embed_resources,
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

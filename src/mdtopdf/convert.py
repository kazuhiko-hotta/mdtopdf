from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


@dataclass(frozen=True)
class ConvertOptions:
    css_paths: tuple[Path, ...]
    use_default_css: bool
    paper: str
    margin: str
    table_font_size: str
    font_family: str
    browser: str
    timeout_ms: int
    embed_resources: bool


def convert_markdown_files(
    inputs: Iterable[Path],
    *,
    output_path: Path | None,
    outdir: Path | None,
    css_paths: list[Path],
    use_default_css: bool,
    paper: str,
    margin: str,
    table_font_size: str,
    font_family: str,
    browser: str,
    timeout_ms: int,
    embed_resources: bool,
) -> bool:
    options = ConvertOptions(
        css_paths=tuple(css_paths),
        use_default_css=use_default_css,
        paper=paper,
        margin=margin,
        table_font_size=table_font_size,
        font_family=font_family,
        browser=browser,
        timeout_ms=timeout_ms,
        embed_resources=embed_resources,
    )

    all_ok = True
    inputs_list = list(inputs)

    with sync_playwright() as p:
        browser_launcher = getattr(p, options.browser)
        launch_args = [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
        ]
        if options.browser == "chromium":
            executable_path = os.environ.get("MDTOPDF_CHROMIUM_EXECUTABLE")
            browser = browser_launcher(
                executable_path=executable_path,
                args=launch_args,
            )
        else:
            browser = browser_launcher(args=launch_args)
        try:
            for md_path in inputs_list:
                if output_path is not None:
                    pdf_path = output_path
                elif outdir is not None:
                    pdf_path = outdir / (md_path.stem + ".pdf")
                else:
                    pdf_path = md_path.with_suffix(".pdf")

                try:
                    pdf_path.parent.mkdir(parents=True, exist_ok=True)
                    _convert_one_with_browser(md_path, pdf_path, options, browser)
                    print(f"[ok] {md_path} -> {pdf_path}")
                except Exception as e:  # noqa: BLE001
                    all_ok = False
                    stage = getattr(e, "_mdtopdf_stage", None)
                    prefix = f"[error:{stage}]" if stage else "[error]"
                    print(f"{prefix} {md_path}: {e}", file=sys.stderr)
        finally:
            browser.close()

    return all_ok


def _convert_one(md_path: Path, pdf_path: Path, options: ConvertOptions) -> None:
    with tempfile.TemporaryDirectory(prefix="mdtopdf-") as tmpdir_s:
        tmpdir = Path(tmpdir_s)
        html_path = tmpdir / "doc.html"
        html_text = _md_to_html(md_path, options)
        html_path.write_text(html_text, encoding="utf-8")
        _html_to_pdf_playwright(html_path, pdf_path, options)


def _convert_one_with_browser(
    md_path: Path, pdf_path: Path, options: ConvertOptions, browser
) -> None:
    with tempfile.TemporaryDirectory(prefix="mdtopdf-") as tmpdir_s:
        tmpdir = Path(tmpdir_s)
        html_path = tmpdir / "doc.html"
        html_text = _md_to_html(md_path, options)
        html_path.write_text(html_text, encoding="utf-8")
        _html_to_pdf_with_browser(html_path, pdf_path, options, browser)


def _md_to_html(md_path: Path, options: ConvertOptions) -> str:
    try:
        html = _pandoc_markdown_to_html(
            md_path, embed_resources=options.embed_resources
        )
    except FileNotFoundError as e:
        _tag_stage(e, "pandoc")
        raise FileNotFoundError(
            "pandoc not found. Install pandoc and ensure it is on PATH."
        ) from e
    except subprocess.CalledProcessError as e:
        err = (e.stderr or b"").decode("utf-8", errors="replace").strip()
        ex = RuntimeError(f"pandoc failed (exit {e.returncode}). {err}".strip())
        _tag_stage(ex, "pandoc")
        raise ex from e

    base_href = md_path.parent.resolve().as_uri() + "/"
    html = _insert_base_href(html, base_href)

    css_chunks: list[str] = []
    if options.use_default_css:
        css_chunks.append(_read_default_css())
    for p in options.css_paths:
        css_chunks.append(Path(p).read_text(encoding="utf-8"))

    css_chunks.append(
        "\n".join(
            [
                f"@page {{ size: {options.paper}; margin: {options.margin}; }}",
                f"body {{ font-family: {options.font_family}; }}",
                f"table {{ font-size: {options.table_font_size}; }}",
            ]
        )
    )

    html = _inject_style_tag(
        html, "\n\n".join(chunk for chunk in css_chunks if chunk.strip())
    )
    return html


def _get_pandoc_version() -> tuple[int, ...]:
    try:
        result = subprocess.run(
            ["pandoc", "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        first_line = result.stdout.decode("utf-8").splitlines()[0]
        match = re.search(r"(\d+)\.(\d+)", first_line)
        if match:
            return (int(match.group(1)), int(match.group(2)))
    except (subprocess.CalledProcessError, FileNotFoundError, IndexError):
        pass
    return (0, 0)


def _pandoc_markdown_to_html(md_path: Path, *, embed_resources: bool) -> str:
    common_args = [
        "pandoc",
        str(md_path),
        "--from=gfm",
        "--to=html5",
        "--standalone",
    ]
    if embed_resources:
        version = _get_pandoc_version()
        if version >= (2, 19):
            try:
                return subprocess.run(
                    [*common_args, "--embed-resources"],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                ).stdout.decode("utf-8")
            except subprocess.CalledProcessError:
                pass

        return subprocess.run(
            [*common_args, "--self-contained"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout.decode("utf-8")

    return subprocess.run(
        common_args,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.decode("utf-8")


def _html_to_pdf_with_browser(
    html_path: Path, pdf_path: Path, options: ConvertOptions, browser
) -> None:
    url = html_path.resolve().as_uri()
    try:
        page = browser.new_page()
        page.emulate_media(media="print")
        page.goto(url, wait_until="networkidle", timeout=options.timeout_ms)
        page.pdf(
            path=str(pdf_path),
            print_background=True,
            prefer_css_page_size=True,
        )
    except PlaywrightTimeoutError as e:
        ex = TimeoutError(f"Playwright timed out after {options.timeout_ms}ms")
        _tag_stage(ex, "playwright")
        raise ex from e
    except PlaywrightError as e:
        msg = str(e)
        hint = ""
        if "Executable doesn't exist" in msg or "browserType.launch" in msg:
            hint = " (Did you run: python -m playwright install chromium ?)"
        ex = RuntimeError(f"Playwright failed: {msg}{hint}")
        _tag_stage(ex, "playwright")
        raise ex from e


def _html_to_pdf_playwright(
    html_path: Path, pdf_path: Path, options: ConvertOptions
) -> None:
    url = html_path.resolve().as_uri()
    try:
        with sync_playwright() as p:
            browser_launcher = getattr(p, options.browser)
            launch_args = [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
            ]
            if options.browser == "chromium":
                executable_path = os.environ.get("MDTOPDF_CHROMIUM_EXECUTABLE")
                browser = browser_launcher(
                    executable_path=executable_path,
                    args=launch_args,
                )
            else:
                browser = browser_launcher(args=launch_args)
            try:
                page = browser.new_page()
                page.emulate_media(media="print")
                page.goto(url, wait_until="networkidle", timeout=options.timeout_ms)
                page.pdf(
                    path=str(pdf_path),
                    print_background=True,
                    prefer_css_page_size=True,
                )
            finally:
                browser.close()
    except PlaywrightTimeoutError as e:
        ex = TimeoutError(f"Playwright timed out after {options.timeout_ms}ms")
        _tag_stage(ex, "playwright")
        raise ex from e
    except PlaywrightError as e:
        msg = str(e)
        hint = ""
        if "Executable doesn't exist" in msg or "browserType.launch" in msg:
            hint = f" (Did you run: python -m playwright install {options.browser} ?)"
        ex = RuntimeError(f"Playwright failed: {msg}{hint}")
        _tag_stage(ex, "playwright")
        raise ex from e


def _read_default_css() -> str:
    from importlib.resources import files

    return (files("mdtopdf") / "assets" / "default.css").read_text(encoding="utf-8")


def _insert_base_href(html: str, base_href: str) -> str:
    match = re.search(r"<head\b[^>]*>", html, re.IGNORECASE)
    if not match:
        return html
    insert_at = match.end()
    return html[:insert_at] + f'\n  <base href="{base_href}">' + html[insert_at:]


def _inject_style_tag(html: str, css: str) -> str:
    match = re.search(r"</head>", html, re.IGNORECASE)
    if not match:
        return html + f"\n<style>\n{css}\n</style>\n"
    style_tag = f"\n<style>\n{css}\n</style>\n"
    return html[: match.start()] + style_tag + html[match.start() :]


def _tag_stage(exc: Exception, stage: str) -> None:
    setattr(exc, "_mdtopdf_stage", stage)

from __future__ import annotations

import unittest
import re


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


class TestConvertUtils(unittest.TestCase):
    def test_insert_base_href(self) -> None:
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Test</title>
</head>
<body>
    <h1>Hello World</h1>
</body>
</html>"""

        base_href = "https://example.com/"
        result = _insert_base_href(html, base_href)

        self.assertIn('<base href="https://example.com/">', result)

    def test_insert_base_href_no_head(self) -> None:
        html = """<!DOCTYPE html>
<html>
<body>
    <h1>Hello World</h1>
</body>
</html>"""

        base_href = "https://example.com/"
        result = _insert_base_href(html, base_href)

        self.assertEqual(result, html)

    def test_insert_base_href_with_attributes(self) -> None:
        html = """<!DOCTYPE html>
<html lang="en">
<head prefix="og: http://ogp.me/ns#">
    <title>Test</title>
</head>
<body>
    <h1>Hello World</h1>
</body>
</html>"""

        base_href = "https://example.com/"
        result = _insert_base_href(html, base_href)

        self.assertIn('<base href="https://example.com/">', result)

    def test_inject_style_tag(self) -> None:
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Test</title>
</head>
<body>
    <h1>Hello World</h1>
</body>
</html>"""

        css = "body { color: red; }"
        result = _inject_style_tag(html, css)

        self.assertIn("<style>", result)
        self.assertIn("body { color: red; }", result)
        self.assertIn("</style>", result)

    def test_inject_style_tag_no_head(self) -> None:
        html = """<!DOCTYPE html>
<html>
<body>
    <h1>Hello World</h1>
</body>
</html>"""

        css = "body { color: red; }"
        result = _inject_style_tag(html, css)

        self.assertIn("<style>", result)
        self.assertIn("</style>", result)

    def test_inject_empty_css(self) -> None:
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Test</title>
</head>
<body>
    <h1>Hello World</h1>
</body>
</html>"""

        css = ""
        result = _inject_style_tag(html, css)

        self.assertIn("<style>", result)
        self.assertIn("</style>", result)


if __name__ == "__main__":
    unittest.main()

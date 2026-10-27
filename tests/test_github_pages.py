"""Guards for the published site in github-pages/."""
import base64
import hashlib
import json
import re
import unittest
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "github-pages"
PAGES = {"index.html": (SITE / "index.html").read_text(encoding="utf-8")}
INDEX = PAGES["index.html"]


class CspHashTest(unittest.TestCase):
    def test_inline_scripts_match_csp_hashes(self):
        csp = re.search(r'Content-Security-Policy" content="([^"]*)"', INDEX).group(1)
        allowed = set(re.findall(r"'sha256-([^']+)'", csp))
        inline = [s for attrs, s in re.findall(r"<script([^>]*)>(.*?)</script>", INDEX, re.S)
                  if "src=" not in attrs and "ld+json" not in attrs]
        self.assertTrue(inline, "expected the inline theme script")
        for body in inline:
            digest = base64.b64encode(hashlib.sha256(body.encode()).digest()).decode()
            self.assertIn(digest, allowed, "inline script changed: recompute the sha256 in the CSP meta tag")


class EveryPageTest(unittest.TestCase):
    def test_inline_scripts_match_csp_hashes_on_every_page(self):
        for name, html in PAGES.items():
            csp = re.search(r'Content-Security-Policy" content="([^"]*)"', html).group(1)
            allowed = set(re.findall(r"'sha256-([^']+)'", csp))
            for attrs, body in re.findall(r"<script([^>]*)>(.*?)</script>", html, re.S):
                if "src=" in attrs or "ld+json" in attrs:
                    continue
                digest = base64.b64encode(hashlib.sha256(body.encode()).digest()).decode()
                self.assertIn(digest, allowed, f"{name}: inline script changed, recompute the CSP hash")

    def test_one_main_one_h1_and_no_inline_styles(self):
        for name, html in PAGES.items():
            self.assertEqual(html.count("<main"), 1, name)
            self.assertEqual(html.count("<h1"), 1, name)
            self.assertNotIn(' style="', html, name)

    def test_every_figure_has_an_accessible_name(self):
        idea = INDEX
        figures = [a for a in re.findall(r'<svg viewBox="[^"]*"([^>]*)>', idea) if "aria-hidden" not in a]
        self.assertGreaterEqual(len(figures), 6)
        for attrs in figures:
            self.assertIn('role="img"', attrs)
            self.assertRegex(attrs, r'aria-label="[^"]{20,}"')

    def test_skills_named_on_every_page_exist(self):
        skills = {p.name for p in (SITE.parent / ".agents" / "skills").iterdir() if p.is_dir()}
        for name, html in PAGES.items():
            named = set(re.findall(r"<code>(wiki(?:-[a-z]+)?)</code>", html))
            self.assertFalse(named - skills, f"{name} names skills that do not exist: {sorted(named - skills)}")

    def test_single_page_journey(self):
        # The page is one document: no separate idea page, five numbered parts, and every nav and reading-order link has a target.
        self.assertFalse((SITE / "idea.html").exists())
        ids = set(re.findall(r'<section[^>]*id="([^"]+)"', INDEX))
        parts = re.findall(r'<p class="eyebrow"><span class="num">(\d)</span>', INDEX)
        self.assertEqual(parts, ["1", "2", "3", "4", "5"])
        links = re.findall(r'<a (?:class="chip" )?href="#([a-z-]+)"', INDEX)
        self.assertTrue(links)
        self.assertFalse(set(links) - ids - {"content", "top"}, sorted(set(links) - ids))
        order = re.findall(r'<section[^>]*id="([^"]+)"', INDEX)
        self.assertLess(order.index("operations"), order.index("graph"), "the graph comes after the three operations it plays out")
        self.assertLess(order.index("graph"), order.index("inputs"))


class PwaTest(unittest.TestCase):
    def test_manifest_icons_exist(self):
        manifest = json.loads((SITE / "manifest.webmanifest").read_text(encoding="utf-8"))
        for icon in manifest["icons"]:
            self.assertTrue((SITE / icon["src"]).is_file(), icon["src"])

    def test_service_worker_precache_exists(self):
        sw = (SITE / "sw.js").read_text(encoding="utf-8")
        block = re.search(r"PRECACHE = \[(.*?)\]", sw, re.S).group(1)
        for path in re.findall(r"'\./([^']*)'", block):
            self.assertTrue((SITE / (path or "index.html")).is_file(), path)

    def test_page_links_manifest_and_assets(self):
        for ref in ("manifest.webmanifest", "assets/site.css", "assets/i18n.js", "assets/graph.js", "assets/app.js"):
            self.assertIn(ref, INDEX)
            self.assertTrue((SITE / ref).is_file(), ref)


class GraphWiringTest(unittest.TestCase):
    def test_every_element_id_the_scripts_use_exists(self):
        ids = set(re.findall(r'id="([^"]+)"', INDEX))
        for name in ("graph.js", "app.js"):
            src = (SITE / "assets" / name).read_text(encoding="utf-8")
            used = set(re.findall(r"(?:\$|getElementById)\('([A-Za-z0-9_-]+)'\)", src)) | set(re.findall(r"\bon\('([A-Za-z0-9_-]+)'", src))
            self.assertFalse(used - ids, f"{name} uses ids missing from index.html: {sorted(used - ids)}")


class SkillNamesTest(unittest.TestCase):
    def test_skills_named_on_the_page_exist(self):
        skills = {p.name for p in (SITE.parent / ".agents" / "skills").iterdir() if p.is_dir()}
        named = set(re.findall(r"<code>(wiki(?:-[a-z]+)?)</code>", INDEX))
        self.assertTrue({"wiki-ingest", "wiki-query", "wiki-maintenance"} <= named)
        self.assertFalse(named - skills, f"page names skills that do not exist: {sorted(named - skills)}")

    def test_slash_commands_on_the_page_exist(self):
        commands = {p.stem for p in (SITE.parent / ".agents" / "commands").glob("*.md")}
        shown = set(re.findall(r"<code>/(wiki[a-z-]*)</code>", INDEX))
        self.assertTrue(shown)
        self.assertFalse(shown - commands, sorted(shown - commands))


class MarkupTest(unittest.TestCase):
    def test_single_main_and_h1(self):
        self.assertEqual(INDEX.count("<main"), 1)
        self.assertEqual(INDEX.count("<h1"), 1)

    def test_no_inline_style_attributes(self):
        self.assertNotIn(' style="', INDEX)


if __name__ == "__main__":
    unittest.main()

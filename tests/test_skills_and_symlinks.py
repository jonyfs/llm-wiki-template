from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / ".agents" / "skills"
COMMANDS_DIR = REPO_ROOT / ".agents" / "commands"
REQUIRED_SKILLS = {"wiki", "wiki-ingest", "wiki-maintenance", "wiki-query", "wiki-router", "wiki-update", "wiki-writing"}
FRONTMATTER_KEY = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$")


def read_frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fields: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return fields
        match = FRONTMATTER_KEY.match(line)
        if match:
            fields[match.group(1)] = match.group(2).strip()
    return {}


class SkillFrontmatterTests(unittest.TestCase):
    def test_required_playbook_skills_exist(self) -> None:
        present = {path.name for path in SKILLS_DIR.iterdir() if path.is_dir()}
        self.assertTrue(REQUIRED_SKILLS <= present, f"missing skills: {sorted(REQUIRED_SKILLS - present)}")

    def test_every_skill_has_name_and_description(self) -> None:
        for skill_dir in sorted(path for path in SKILLS_DIR.iterdir() if path.is_dir()):
            with self.subTest(skill=skill_dir.name):
                skill_file = skill_dir / "SKILL.md"
                self.assertTrue(skill_file.is_file(), "SKILL.md missing")
                fields = read_frontmatter(skill_file)
                self.assertTrue(fields.get("name"), "frontmatter name missing")
                self.assertTrue(fields.get("description"), "frontmatter description missing")


class AgentMirrorTests(unittest.TestCase):
    """Agent entry points must be real copies, never symlinks, so Windows checkouts keep working."""

    MIRRORS = {
        "CLAUDE.md": "AGENTS.md",
        ".cursorrules": "AGENTS.md",
        ".github/copilot-instructions.md": "AGENTS.md",
        ".claude/skills": ".agents/skills",
        ".claude/commands": ".agents/commands",
        ".opencode/skills": ".agents/skills",
        ".opencode/commands": ".agents/commands",
    }

    def test_mirrors_are_real_files_and_folders_not_symlinks(self) -> None:
        for target in self.MIRRORS:
            with self.subTest(target=target):
                path = REPO_ROOT / target
                self.assertFalse(path.is_symlink(), f"{target} must not be a symlink")
                self.assertTrue(path.exists(), f"{target} is missing")

    def test_mirrors_match_their_sources(self) -> None:
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "sync_agent_files.py"), "--check"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_manifest_mirror_lines_cover_every_mirror(self) -> None:
        manifest = (REPO_ROOT / ".agents" / "template-manifest").read_text(encoding="utf-8")
        declared = {
            parts[1]: parts[2]
            for parts in (line.split("\t") for line in manifest.splitlines())
            if len(parts) == 3 and parts[0] == "mirror"
        }
        self.assertEqual(declared, self.MIRRORS)


if __name__ == "__main__":
    unittest.main()

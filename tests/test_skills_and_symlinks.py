from __future__ import annotations

import os
import re
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


class SymlinkTests(unittest.TestCase):
    def assert_symlink_to(self, link: str, target: Path) -> None:
        path = REPO_ROOT / link
        self.assertTrue(path.is_symlink(), f"{link} is not a symlink")
        self.assertEqual(Path(os.path.realpath(path)), target.resolve(), f"{link} does not resolve to {target}")

    def test_skill_folders_resolve_to_agents_skills(self) -> None:
        self.assert_symlink_to(".claude/skills", SKILLS_DIR)
        self.assert_symlink_to(".opencode/skills", SKILLS_DIR)

    def test_command_folders_resolve_to_agents_commands(self) -> None:
        self.assert_symlink_to(".claude/commands", COMMANDS_DIR)
        self.assert_symlink_to(".opencode/commands", COMMANDS_DIR)

    def test_agent_instruction_files_resolve_to_agents_md(self) -> None:
        agents_md = REPO_ROOT / "AGENTS.md"
        for link in ("CLAUDE.md", ".cursorrules", ".github/copilot-instructions.md"):
            with self.subTest(link=link):
                self.assert_symlink_to(link, agents_md)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "benchmark.py"


class BenchmarkScriptTests(unittest.TestCase):
    def run_benchmark(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_benchmark_times_lint_and_refresh_on_synthetic_wiki(self) -> None:
        result = self.run_benchmark("--pages", "30")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("pages: 30", result.stdout)
        self.assertIn("lint: ", result.stdout)
        self.assertIn("refresh: ", result.stdout)
        self.assertIn("lint violations: 0", result.stdout)

    def test_benchmark_profile_prints_hotspots(self) -> None:
        result = self.run_benchmark("--pages", "30", "--profile")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("cumtime", result.stdout)


if __name__ == "__main__":
    unittest.main()

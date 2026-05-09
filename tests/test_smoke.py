"""Smoke tests — verify the package wires up correctly without hitting Overleaf."""

import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import claude_to_overleaf
from claude_to_overleaf import cli


class TestPackageMetadata(unittest.TestCase):
    def test_version_exposed(self):
        self.assertIsInstance(claude_to_overleaf.__version__, str)
        self.assertRegex(claude_to_overleaf.__version__, r"^\d+\.\d+\.\d+")

    def test_main_callable(self):
        self.assertTrue(callable(cli.main))


class TestEnvFileParsing(unittest.TestCase):
    def test_parses_simple_kv(self):
        with TemporaryDirectory() as d:
            p = Path(d) / ".env"
            p.write_text("FOO=bar\nBAZ=qux\n")
            self.assertEqual(cli.load_env_file(p), {"FOO": "bar", "BAZ": "qux"})

    def test_skips_comments_and_blank_lines(self):
        with TemporaryDirectory() as d:
            p = Path(d) / ".env"
            p.write_text("# a comment\n\nFOO=bar\n  # another\nBAZ=qux\n")
            self.assertEqual(cli.load_env_file(p), {"FOO": "bar", "BAZ": "qux"})

    def test_strips_surrounding_quotes(self):
        with TemporaryDirectory() as d:
            p = Path(d) / ".env"
            p.write_text('FOO="bar"\nBAZ=\'qux\'\n')
            self.assertEqual(cli.load_env_file(p), {"FOO": "bar", "BAZ": "qux"})

    def test_missing_file_returns_empty(self):
        self.assertEqual(cli.load_env_file(Path("/no/such/file/.env")), {})


class TestUrlBuilding(unittest.TestCase):
    def test_token_is_url_encoded(self):
        cfg = {"token": "olp_abc/def", "project_id": "deadbeef"}
        url = cli.overleaf_url(cfg)
        self.assertIn("olp_abc%2Fdef", url)
        self.assertIn("git.overleaf.com/deadbeef", url)
        self.assertTrue(url.startswith("https://git:"))


class TestRequire(unittest.TestCase):
    def test_missing_keys_uses_env_var_names_in_message(self):
        with self.assertRaises(SystemExit) as ctx:
            cli.require({}, "token", "project_id")
        msg = str(ctx.exception)
        self.assertIn("OVERLEAF_TOKEN", msg)
        self.assertIn("OVERLEAF_PROJECT_ID", msg)

    def test_present_keys_pass(self):
        cli.require({"token": "x", "project_id": "y"}, "token", "project_id")


class TestSkillBundling(unittest.TestCase):
    def test_skill_file_shipped_with_package(self):
        skill = Path(claude_to_overleaf.__file__).parent / "SKILL.md"
        self.assertTrue(skill.exists(), f"SKILL.md missing at {skill}")
        text = skill.read_text()
        self.assertIn("name: claude-to-overleaf", text)
        self.assertIn("sync to overleaf", text.lower())

    def test_install_skill_writes_to_target(self):
        with TemporaryDirectory() as fake_home:
            with patch.dict(os.environ, {"HOME": fake_home}):
                cli.cmd_install_skill()
            target = Path(fake_home) / ".claude" / "skills" / "claude-to-overleaf" / "SKILL.md"
            self.assertTrue(target.exists())
            self.assertIn("name: claude-to-overleaf", target.read_text())


class TestEntryPoint(unittest.TestCase):
    """Run the installed module the same way users will."""

    def test_help_runs(self):
        env = os.environ.copy()
        result = subprocess.run(
            [sys.executable, "-m", "claude_to_overleaf", "--help"],
            capture_output=True,
            text=True,
            env=env,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("setup", result.stdout)
        self.assertIn("sync", result.stdout)


if __name__ == "__main__":
    unittest.main()

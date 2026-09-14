import contextlib
import importlib.util
import io
import json
import shutil
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    "configs", Path(__file__).resolve().parents[1] / "scripts/install-agent-configs.py"
)
configs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(configs)


class AgentConfigsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.root = self.home / "dev/dotfiles"
        self.root.mkdir(parents=True)
        for source in ("claude-settings.json", "codex-config.toml"):
            shutil.copy2(configs.REPO / source, self.root / source)

    def install(self):
        with contextlib.redirect_stdout(io.StringIO()):
            configs.install(self.home, self.root)

    def test_migration_overrides_and_app_edits(self):
        target = self.home / ".codex/config.toml"
        target.parent.mkdir()
        original = 'model = "local-model"\n[projects."/some/machine/path"]\ntrust_level = "trusted"\n'
        target.write_text(original)
        self.install()
        self.assertTrue(target.is_symlink())
        self.assertEqual(target.resolve(), (self.root / "agents/codex-config.toml").resolve())
        self.assertEqual(
            (self.home / ".claude/settings.json").resolve(),
            (self.root / "agents/claude-config.json").resolve(),
        )
        self.assertFalse((self.home / ".config").exists())
        self.assertEqual(target.with_name("config.toml.pre-dotfiles").read_text(), original)
        self.assertEqual(configs.read(target)["model"], "local-model")
        self.assertNotIn("projects", configs.read(target))
        imported = configs.read(self.root / "codex.d/00-imported.toml")
        self.assertEqual(imported, {"model": "local-model"})
        self.install()
        self.assertNotIn("projects", configs.read(target))
        (self.root / "codex.d/90-local.toml").write_text('[tui]\nshow_tooltips = true\n')
        self.install()
        self.assertTrue(configs.read(target)["tui"]["show_tooltips"])
        self.assertIn("status_line", configs.read(target)["tui"])
        # Simulate an app atomically replacing the symlink.
        text = target.read_text()
        target.unlink()
        target.write_text(text + '\n[app_state]\nchanged = true\n')
        with self.assertRaisesRegex(ValueError, "changed since installation"):
            self.install()
        self.assertIn("app_state", configs.read(target))

    def test_invalid_fragment_does_not_touch_destinations(self):
        fragments = self.root / "codex.d"
        fragments.mkdir(parents=True)
        (fragments / "bad.toml").write_text('broken = [')
        with self.assertRaises(ValueError):
            self.install()
        self.assertFalse((self.home / ".claude/settings.json").exists())

    def test_fragment_order_and_array_replacement(self):
        self.install()
        fragments = self.root / "claude.d"
        (fragments / "10-local.json").write_text(json.dumps({"permissions": {"allow": ["first"]}}))
        (fragments / "90-local.json").write_text(json.dumps({"permissions": {"allow": ["last"]}}))
        self.install()
        permissions = configs.read(self.home / ".claude/settings.json")["permissions"]
        self.assertEqual(permissions["allow"], ["last"])
        self.assertEqual(permissions["defaultMode"], "auto")


if __name__ == "__main__":
    unittest.main()

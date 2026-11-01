import os
import tempfile
import unittest
import importlib.util
from pathlib import Path

# Load the script under test from PYPROJECT_SCRIPT (set by the ./unit_test
# runner: PYPROJECT_SCRIPT=$PWD/../src/app/main.py)
SCRIPT_PATH = os.environ.get("PYPROJECT_SCRIPT")
if SCRIPT_PATH:
    spec = importlib.util.spec_from_file_location("main", SCRIPT_PATH)
    main = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main)
else:
    # Fallback: run directly with python3 tests/unit_test.py
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
    import main


class TestProject(unittest.TestCase):

    def test_version(self):
        self.assertEqual(main.VERSION, "1.4.0")

    def test_is_valid_project_name(self):
        self.assertTrue(main.is_valid_project_name("my_tool"))
        self.assertTrue(main.is_valid_project_name("My-Tool2"))
        self.assertFalse(main.is_valid_project_name("2tool"))
        self.assertFalse(main.is_valid_project_name("my tool"))
        self.assertFalse(main.is_valid_project_name(""))

    def test_normalize_version(self):
        self.assertEqual(main.normalize_version("v1.0.1"), "1.0.1")
        self.assertEqual(main.normalize_version("1.0.1"), "1.0.1")
        self.assertIsNone(main.normalize_version("abc"))
        self.assertIsNone(main.normalize_version("v1.x.2"))

    def test_suggest_next_version(self):
        self.assertEqual(main.suggest_next_version("1.0.0"), "1.0.1")
        self.assertEqual(main.suggest_next_version("0.0.1"), "0.0.2")
        self.assertEqual(main.suggest_next_version("2.5.9"), "2.5.10")

    def test_apply_version_updates_all_three_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "pyproject.toml").write_text(
                '[project]\nname = "demo"\nversion = "1.0.0"\n'
            )
            pkg = project / "src" / "app"
            pkg.mkdir(parents=True)
            (pkg / "__init__.py").write_text('__version__ = "1.0.0"\n')
            tests = project / "tests"
            tests.mkdir()
            (tests / "unit_test.py").write_text(
                'self.assertEqual(app.__version__, "1.0.0")\n'
            )

            main.apply_version_update(project, "1.0.0", "1.0.1")

            self.assertIn('version = "1.0.1"',
                          (project / "pyproject.toml").read_text())
            self.assertIn('__version__ = "1.0.1"',
                          (pkg / "__init__.py").read_text())
            self.assertIn('"1.0.1"',
                          (tests / "unit_test.py").read_text())

    def test_read_project_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "pyproject.toml").write_text(
                '[project]\nname = "demo"\nversion = "2.3.4"\n'
            )
            self.assertEqual(main.read_project_version(project), "2.3.4")
            self.assertEqual(main.read_project_name(project), "demo")


if __name__ == "__main__":
    unittest.main()

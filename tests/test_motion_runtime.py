"""Exercise the public film bundle, including the legacy transition API."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


class RuntimeBundleTests(unittest.TestCase):
    def test_prepared_bundle_preserves_motion_and_legacy_checks(self):
        spec = importlib.util.spec_from_file_location('prepare_film', ROOT / 'scripts/prepare-film.py')
        prepare = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(prepare)
        evidence = ROOT / 'output/verification'
        evidence.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='motion-runtime-', dir=evidence) as tmp:
            assets = Path(tmp) / 'assets'
            prepare.prepare_libraries(assets)
            result = subprocess.run(['node', str(ROOT / 'tests/motion_runtime.cjs'), str(assets)],
                                    cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()

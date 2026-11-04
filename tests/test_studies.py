import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / 'studies/scripts/verify_library.py'
# studies/ is a local, git-ignored research library; a fresh clone has none.
if LIBRARY.is_file():
    spec = importlib.util.spec_from_file_location('verify_library', LIBRARY)
    verify = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verify)


@unittest.skipUnless(LIBRARY.is_file(), 'local studies/ library is absent')
class BoundaryTests(unittest.TestCase):
    def test_document_can_link_to_repository_skill(self):
        path = verify.local_path(ROOT / 'studies', '../motion/SKILL.md', boundary=ROOT)
        self.assertEqual(path, ROOT / 'motion/SKILL.md')

    def test_evidence_cannot_escape_studies(self):
        with self.assertRaises(ValueError):
            verify.local_path(ROOT / 'studies', '../motion/SKILL.md')

    def test_document_cannot_escape_repository(self):
        with self.assertRaises(ValueError):
            verify.local_path(ROOT / 'studies', '../../', allow_directory=True, boundary=ROOT)


if __name__ == '__main__':
    unittest.main()

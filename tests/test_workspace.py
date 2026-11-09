import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import workspace
import font_assets
import shuyu


class WorkspaceTests(unittest.TestCase):
    def test_prepare_does_not_copy_dotenv_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, dest = root / 'film', root / 'project'
            source.mkdir()
            dest.mkdir()
            (source / 'index.html').write_text('<html></html>')
            (source / '.env').write_text('API_KEY=local-secret')
            (source / '.env.local').write_text('API_KEY=another-secret')
            with patch.object(shuyu, 'ROOT', root), \
                    patch.object(shuyu, 'project_config', return_value={'source': 'film'}), \
                    patch.object(shuyu, 'inside', side_effect=lambda name: root / name), \
                    patch.object(shuyu, 'output_dir', return_value=dest), \
                    patch.object(shuyu, 'check_if_managed'), patch.object(shuyu, 'check_prepared'), \
                    patch.object(shuyu, 'invoke'):
                shuyu.prepare_project('test')
            self.assertTrue((dest / 'index.html').exists())
            self.assertFalse((dest / '.env').exists())
            self.assertFalse((dest / '.env.local').exists())
            self.assertNotIn('.env', (dest / shuyu.SOURCE_MANIFEST).read_text())

    def test_project_outputs_are_independent_of_working_directory(self):
        path = workspace.output_dir('test-film', 'math', 'run-1')
        self.assertEqual(path, ROOT / 'output/test-film/math/run-1')
        for project in ('../motion', 'C:/elsewhere', ''):
            with self.assertRaises(ValueError):
                workspace.output_dir(project)
        with self.assertRaises(ValueError):
            workspace.output_dir('test-film', '..', '..', 'outside')

    def test_registered_versions_override_the_common_default(self):
        self.assertEqual(workspace.hyperframes_version('staircase-test'), '0.8.220')
        self.assertEqual(workspace.hyperframes_version('brand'), workspace.config()['hyperframes'])

    def test_font_cache_reuses_character_sets_without_coupling_outputs(self):
        source = ROOT / 'node_modules/katex/dist/fonts/KaTeX_Main-Regular.ttf'
        if not source.exists():
            self.skipTest('npm ci required')
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            with patch.object(font_assets, 'inside', return_value=directory), \
                 patch.object(font_assets, 'font_path', return_value=source), \
                 patch.object(font_assets, 'font_record', return_value={'faceIndex': 0, 'license': 'OFL-1.1'}):
                a = font_assets.build_subset('sans', 'ABBA', directory / 'one.woff2')
                b = font_assets.build_subset('sans', 'BA', directory / 'two.woff2')
                c = font_assets.build_subset('sans', 'ABC', directory / 'three.woff2')
            self.assertEqual(a['cacheKey'], b['cacheKey'])
            self.assertNotEqual(a['cacheKey'], c['cacheKey'])
            self.assertEqual(len(list((directory / 'fonts').glob('*.woff2'))), 2)
            before = (directory / 'two.woff2').read_bytes()
            (directory / 'one.woff2').write_bytes(b'edited project font')
            self.assertEqual((directory / 'two.woff2').read_bytes(), before)
            self.assertEqual((directory / 'fonts' / (a['cacheKey'] + '.woff2')).read_bytes(), before)


if __name__ == '__main__':
    unittest.main()

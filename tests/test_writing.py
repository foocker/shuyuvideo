import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'writing'))
import manuscript as writing


class WritingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.film = Path(self.tmp.name)
        self.config = {
            'voice': 'zh-CN-YunxiNeural', 'rate': '-3%', 'gap': .35, 'lead': .5,
            'tail': 1.2, 'bedGain': .08, 'extension': {'keep': [1, '中文', False]},
            'lines': [
                {'id': 'a1', 'scene': 'overlap', 'text': '同一个点，有两套坐标。', 'pause': .8, 'custom': 12},
                {'id': 'a2', 'scene': 'overlap', 'text': '先固定这个点。\n再换坐标。', 'start': 10},
            ],
        }
        self.write_json('narration.json', self.config)

    def write_json(self, name, value):
        (self.film / name).write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')

    def import_script(self):
        writing.import_script(self.film)
        return self.film / 'SCRIPT.md'

    def edit(self, old, new):
        path = self.film / 'SCRIPT.md'
        path.write_text(path.read_text(encoding='utf-8').replace(old, new), encoding='utf-8')

    def test_lossless_roundtrip_preserves_all_settings_order_and_extensions(self):
        self.import_script()
        original_bytes = (self.film / 'narration.json').read_bytes()
        report = writing.export_script(self.film)
        self.assertFalse(report['changed'])
        self.assertEqual((self.film / 'narration.json').read_bytes(), original_bytes)
        self.assertEqual(writing.parse((self.film / 'SCRIPT.md').read_text(encoding='utf-8')), self.config)
        self.assertTrue(writing.check_project(self.film)['ok'])

    def test_text_edit_preserves_configuration_and_requires_export(self):
        self.import_script()
        self.edit('同一个点，有两套坐标。', '固定这个点，看它在两张图里的坐标。')
        with self.assertRaisesRegex(ValueError, 'disagree'):
            writing.check_if_managed(self.film)
        report = writing.export_script(self.film)
        expected = copy.deepcopy(self.config)
        expected['lines'][0]['text'] = '固定这个点，看它在两张图里的坐标。'
        self.assertEqual(writing.read_json(self.film / 'narration.json'), expected)
        self.assertEqual(report['changedLines'], ['a1'])
        self.assertTrue(report['requiresAudioRefresh'])
        writing.check_project(self.film)

    def test_dry_run_does_not_write_or_register_a_new_project(self):
        (self.film / 'narration.json').unlink()
        (self.film / 'SCRIPT.md').write_text(writing.format_script(self.config), encoding='utf-8')
        before = {p.name: p.read_bytes() for p in self.film.iterdir()}
        report = writing.export_script(self.film, dry_run=True)
        self.assertTrue(report['dryRun'])
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.film.iterdir()})
        writing.export_script(self.film)
        writing.check_project(self.film)

    def test_import_will_not_replace_an_existing_draft(self):
        (self.film / 'SCRIPT.md').write_text('待编辑的旧稿', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'never overwrites'):
            writing.import_script(self.film)
        self.assertEqual((self.film / 'SCRIPT.md').read_text(encoding='utf-8'), '待编辑的旧稿')
        writing.import_script(self.film, 'SCRIPT.writing.md')
        (self.film / 'SCRIPT.md').write_text('旧构建更新了展示稿', encoding='utf-8')
        self.assertEqual(writing.check_project(self.film)['script'], 'SCRIPT.writing.md')

    def test_external_json_edits_are_not_silently_overwritten(self):
        self.import_script()
        self.edit('同一个点', '同一个位置')
        self.config['rate'] = '+5%'
        self.write_json('narration.json', self.config)
        before = {p.name: p.read_bytes() for p in self.film.iterdir()}
        with self.assertRaisesRegex(ValueError, 'outside writing'):
            writing.export_script(self.film)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.film.iterdir()})

    def test_repeated_export_recovers_after_state_write_failure(self):
        self.import_script()
        self.edit('同一个点', '同一个位置')
        with patch.object(writing, 'save_state', side_effect=OSError('disk interrupted')):
            with self.assertRaises(OSError):
                writing.export_script(self.film)
        with self.assertRaisesRegex(ValueError, 'stale'):
            writing.check_project(self.film)
        writing.export_script(self.film)
        writing.check_project(self.film)

    def test_atomic_replace_failure_keeps_previous_narration(self):
        self.import_script()
        self.edit('同一个点', '同一个位置')
        before = (self.film / 'narration.json').read_bytes()
        with patch.object(writing.os, 'replace', side_effect=OSError('locked')):
            with self.assertRaises(OSError):
                writing.export_script(self.film)
        self.assertEqual((self.film / 'narration.json').read_bytes(), before)
        self.assertEqual({p.name for p in self.film.iterdir()}, {'SCRIPT.md', 'narration.json', '.writing.json'})

    def test_director_notes_do_not_enter_spoken_output(self):
        self.import_script()
        (self.film / 'DIRECTION.md').write_text('暂停画面，显示公式 $x^2$。', encoding='utf-8')
        writing.export_script(self.film)
        self.assertEqual(writing.read_json(self.film / 'narration.json'), self.config)
        self.edit('# 口播稿', '# 口播稿\n\n暂停画面，显示公式。')
        with self.assertRaisesRegex(ValueError, 'outside spoken blocks'):
            writing.export_script(self.film)
        self.assertEqual(writing.read_json(self.film / 'narration.json'), self.config)

    def test_invalid_input_does_not_replace_output(self):
        original = writing.format_script(self.config)
        variants = [
            original.replace('"id": "a2"', '"id": "A1"'),
            original.replace('"id": "a1"', '"id": "../escape"'),
            original.replace('"id": "a1"', '"id": "CON"'),
            original.replace('"pause": 0.8', '"pause": -1'),
            original.replace('"pause": 0.8', '"pause": true'),
            original.replace('"pause": 0.8', '"pause": 1e999'),
            original.replace('"pause": 0.8', '"pause": NaN'),
            original.replace('"id": "a1"', '"id": "a1", "id": "a3"'),
            original.replace('同一个点，有两套坐标。', ''),
            original.replace('同一个点，有两套坐标。', '$x^2$'),
            original.replace(writing.END, '', 1),
            original.replace(writing.MARKER, '# 旧构建生成的无标记稿'),
        ]
        before = (self.film / 'narration.json').read_bytes()
        for content in variants:
            with self.subTest(content=content[:65]):
                (self.film / 'SCRIPT.md').write_text(content, encoding='utf-8')
                with self.assertRaises(ValueError):
                    writing.export_script(self.film)
                self.assertEqual((self.film / 'narration.json').read_bytes(), before)

    def test_removed_line_or_anchor_word_is_rejected(self):
        self.write_json('anchors.json', {'point': {'line': 'a1', 'word': '同一个点'}})
        self.import_script()
        self.edit('同一个点', '固定位置')
        with self.assertRaisesRegex(ValueError, 'word or occurrence'):
            writing.export_script(self.film)
        self.write_json('anchors.json', {'point': {'line': 'deleted', 'at': 'start'}})
        with self.assertRaisesRegex(ValueError, 'unknown line'):
            writing.export_script(self.film)

    def test_configuration_and_reordering_also_require_audio_refresh(self):
        self.import_script()
        revised = copy.deepcopy(self.config)
        revised['rate'] = '+5%'
        revised['lines'].reverse()
        (self.film / 'SCRIPT.md').write_text(writing.format_script(revised), encoding='utf-8')
        report = writing.export_script(self.film)
        self.assertTrue(report['requiresAudioRefresh'])
        self.assertEqual(report['changedLines'], [])
        self.assertEqual(writing.read_json(self.film / 'narration.json'), revised)

    def test_json_boolean_and_numeric_extension_values_remain_distinct(self):
        self.import_script()
        revised = copy.deepcopy(self.config)
        revised['extension']['keep'][-1] = 0
        (self.film / 'SCRIPT.md').write_text(writing.format_script(revised), encoding='utf-8')
        report = writing.export_script(self.film)
        self.assertTrue(report['changed'])
        self.assertIs(type(writing.read_json(self.film / 'narration.json')['extension']['keep'][-1]), int)
        writing.check_project(self.film)

    def test_managed_script_path_cannot_escape_project(self):
        for name in ('../SCRIPT.md', '/SCRIPT.md', 'C:/SCRIPT.md', '..\\SCRIPT.md', 'CON.md'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                writing.import_script(self.film, name)

    def test_managed_stale_script_blocks_build_before_invoking_builder(self):
        self.import_script()
        self.edit('同一个点', '同一个位置')
        sys.path.insert(0, str(ROOT / 'scripts'))
        import shuyu
        with patch.object(shuyu, 'project_config', return_value={'source': 'films/sample', 'build': 'build.py'}), \
                patch.object(shuyu, 'inside', return_value=self.film), patch.object(shuyu, 'invoke') as invoke:
            with self.assertRaisesRegex(ValueError, 'disagree'):
                shuyu.prepare_project('sample')
            invoke.assert_not_called()

    def test_managed_stale_script_blocks_audio_validation(self):
        self.import_script()
        self.edit('同一个点', '同一个位置')
        sys.path.insert(0, str(ROOT / 'sound'))
        from audio_state import validate_voice
        with self.assertRaisesRegex(ValueError, 'disagree'):
            validate_voice(self.film, {'lines': []})

    def test_custom_bundle_cannot_drop_management_or_keep_an_old_valid_version(self):
        self.import_script()
        bundle = self.film / 'bundle'
        bundle.mkdir()
        with self.assertRaisesRegex(ValueError, 'lacks writing files'):
            writing.check_prepared(self.film, bundle)
        for name in ('SCRIPT.md', 'narration.json', '.writing.json'):
            shutil.copyfile(self.film / name, bundle / name)
        writing.check_prepared(self.film, bundle)
        self.edit('同一个点', '同一个位置')
        writing.export_script(self.film)
        # Each version is internally consistent, but only the source is current.
        writing.check_project(bundle)
        with self.assertRaisesRegex(ValueError, 'older narration'):
            writing.check_prepared(self.film, bundle)

    def test_unmanaged_legacy_project_is_not_auto_migrated(self):
        self.assertIsNone(writing.check_if_managed(self.film))
        self.assertFalse((self.film / '.writing.json').exists())

    def test_real_example_exports_only_candidate_spoken_blocks(self):
        (self.film / 'narration.json').unlink()
        shutil.copyfile(ROOT / 'examples/writing/SCRIPT.md', self.film / 'SCRIPT.md')
        shutil.copyfile(ROOT / 'examples/writing/DIRECTION.md', self.film / 'DIRECTION.md')
        writing.export_script(self.film)
        exported = writing.read_json(self.film / 'narration.json')
        self.assertEqual(exported['lines'][0]['id'], 'linear1')
        self.assertTrue(any(len(row['text']) > 25 for row in exported['lines']))
        self.assertNotIn('未完成', ''.join(row['text'] for row in exported['lines']))
        writing.check_project(self.film)


if __name__ == '__main__':
    unittest.main()

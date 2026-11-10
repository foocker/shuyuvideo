import contextlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import start
import workspace


class StartTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        shutil.copytree(ROOT / 'scripts/templates', self.root / 'scripts/templates')
        self.root.joinpath('workspace.json').write_text(json.dumps({'projects': {}}), encoding='utf-8')
        for module in (start, workspace):
            mock = patch.object(module, 'ROOT', self.root)
            mock.start()
            self.addCleanup(mock.stop)

    def brief(self, project):
        return (self.root / 'films' / project / 'BRIEF.md').read_text(encoding='utf-8')

    def test_story_mode_defaults_to_no_voices_and_becomes_discoverable(self):
        result = start.start_film('geometry', 'story-animation', title='几何奇遇')
        self.assertEqual(result['omega'], 'off')
        self.assertEqual(result['narration'], 'off')
        self.assertEqual(result['captions'], 'off')
        self.assertIn('mode: story-animation', self.brief('geometry'))
        self.assertIn('narration: "off"', self.brief('geometry'))
        self.assertIn('captions: "off"', self.brief('geometry'))
        self.assertIn('零人声、零台词', self.brief('geometry'))
        self.assertIn('# 几何奇遇', self.brief('geometry'))
        self.assertEqual(workspace.projects()['geometry']['source'], 'films/geometry')
        direction = (self.root / 'films/geometry/DIRECTION.md').read_text(encoding='utf-8')
        self.assertIn('可见后果与下一步动机', direction)
        self.assertIn('声音事件', direction)
        self.assertFalse((self.root / 'films/geometry/index.html').exists())

    def test_explainer_defaults_and_independent_choices(self):
        a = start.start_film('lecture', 'explainer')
        self.assertEqual((a['omega'], a['manim'], a['narration'], a['captions']),
                         ('on', 'auto', 'voiceover', 'on'))
        b = start.start_film('voice-only', 'explainer', omega='off', manim='selected', captions='off')
        self.assertEqual((b['mode'], b['omega'], b['manim'], b['captions']),
                         ('explainer', 'off', 'selected', 'off'))
        c = start.start_film('action', 'story-animation', manim='off', captions='off')
        self.assertEqual((c['omega'], c['manim'], c['captions']), ('off', 'off', 'off'))

    def test_story_voiceover_requires_explicit_choice_and_captions_stay_optional(self):
        a = start.start_film('narrated-story', 'story-animation', narration='voiceover')
        self.assertEqual((a['narration'], a['captions']), ('voiceover', 'off'))
        self.assertIn('画外音剧情变体', self.brief('narrated-story'))
        b = start.start_film('captioned-story', 'story-animation', narration='voiceover', captions='on')
        self.assertEqual((b['narration'], b['captions']), ('voiceover', 'on'))

    def test_speech_captions_cannot_enable_narration_implicitly(self):
        for mode in ('story-animation', 'explainer'):
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, 'requires captions: off'):
                start.start_film('conflict', mode, narration='off', captions='on')
        with self.assertRaisesRegex(ValueError, 'requires captions: off'):
            start.start_film('implicit-voice', 'story-animation', captions='on')
        self.assertFalse((self.root / 'films').exists())

    def test_conflicting_presenter_is_rejected_before_writes(self):
        with self.assertRaisesRegex(ValueError, 'omega: off'):
            start.start_film('conflict', 'story-animation', omega='on')
        self.assertFalse((self.root / 'films').exists())

    def test_existing_work_and_registered_projects_are_never_overwritten(self):
        start.start_film('existing', 'explainer')
        before = self.brief('existing')
        with self.assertRaisesRegex(ValueError, 'already registered'):
            start.start_film('existing', 'story-animation')
        self.assertEqual(self.brief('existing'), before)
        unfinished = self.root / 'films/unfinished'
        unfinished.mkdir()
        (unfinished / 'notes.txt').write_text('keep', encoding='utf-8')
        with self.assertRaises(FileExistsError):
            start.start_film('unfinished', 'explainer')
        self.assertEqual([p.name for p in unfinished.iterdir()], ['notes.txt'])
        self.root.joinpath('workspace.json').write_text(
            json.dumps({'projects': {'registered': {'source': 'examples/demo'}}}), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'already registered'):
            start.start_film('registered', 'explainer')

    def test_bad_paths_and_options_do_not_create_files(self):
        for name in ('../escape', 'C:/escape', '', 'a/b', 'con', 'nul', 'Upper'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                start.start_film(name, 'story-animation')
        for kwargs in ({'mode': 'silent'}, {'mode': 'explainer', 'omega': 'maybe'},
                       {'mode': 'explainer', 'manim': 'never'},
                       {'mode': 'explainer', 'captions': True},
                       {'mode': 'explainer', 'narration': 'auto'},
                       {'mode': 'explainer', 'title': 'title\nmode: other'}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                start.start_film('invalid', **kwargs)
        self.assertFalse((self.root / 'films').exists())

    def test_interactive_choice_and_noninteractive_requirement(self):
        with patch('sys.stdin.isatty', return_value=True), patch('builtins.input', return_value='2'), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(start.main(['interactive']), 0)
        self.assertIn('mode: story-animation', self.brief('interactive'))
        self.assertIn('narration: "off"', self.brief('interactive'))
        with patch('sys.stdin.isatty', return_value=False), contextlib.redirect_stderr(io.StringIO()), \
                self.assertRaises(SystemExit) as failure:
            start.main(['no-selection'])
        self.assertEqual(failure.exception.code, 2)
        self.assertFalse((self.root / 'films/no-selection').exists())

    def test_cli_forwards_explicit_narration_without_changing_story_defaults(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(start.main(['voice-story', '--mode', 'story-animation',
                                         '--narration', 'voiceover', '--captions', 'on']), 0)
            self.assertEqual(start.main(['silent-story', '--mode', 'story-animation']), 0)
        self.assertIn('narration: "voiceover"', self.brief('voice-story'))
        self.assertIn('captions: "on"', self.brief('voice-story'))
        self.assertIn('narration: "off"', self.brief('silent-story'))
        self.assertIn('captions: "off"', self.brief('silent-story'))

    def test_common_entry_dispatches_start_without_creating_a_film(self):
        result = subprocess.run([sys.executable, '-X', 'utf8', str(ROOT / 'scripts/shuyu.py'),
                                 'start', '--help'], cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('story-animation', result.stdout)
        self.assertIn('--captions', result.stdout)
        self.assertIn('--narration', result.stdout)


if __name__ == '__main__':
    unittest.main()

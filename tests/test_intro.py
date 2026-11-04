from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import intro


def fake_projects(records):
    return patch.object(intro, 'project_config', side_effect=lambda name: records[name])


class IntroSwitchTests(unittest.TestCase):
    def test_films_get_the_intro_unless_turned_off(self):
        records = {'film': {'source': 'films/film'}, 'off': {'source': 'films/off', 'brandIntro': False},
                   'brand': {'source': 'brand'}, 'opt-in': {'source': 'examples/x', 'brandIntro': True}}
        with fake_projects(records), patch.object(intro, 'config', return_value={'brandIntro': {'default': True}}):
            self.assertTrue(intro.wanted('film'))
            self.assertFalse(intro.wanted('off'))
            self.assertFalse(intro.wanted('brand'))
            self.assertTrue(intro.wanted('opt-in'))
            # The command-line switch wins over the project setting.
            self.assertFalse(intro.wanted('film', False))
            self.assertTrue(intro.wanted('off', True))

    def test_workspace_default_can_turn_the_intro_off(self):
        with fake_projects({'film': {'source': 'films/film'}}), \
                patch.object(intro, 'config', return_value={'brandIntro': {'default': False}}):
            self.assertFalse(intro.wanted('film'))


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'needs ffmpeg')
class IntroJoinTests(unittest.TestCase):
    def make(self, path, size, seconds, audio):
        command = ['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'color=c=white:s={size}:r=30:d={seconds}']
        if audio:
            command += ['-f', 'lavfi', '-i', f'sine=f=440:sample_rate=48000:d={seconds}', '-ac', '2']
        subprocess.run([*command, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-shortest', str(path)], check=True)

    def test_join_keeps_the_film_canvas_and_adds_both_durations(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            # A silent 4:3 body: the 16:9 intro is fitted inside, and silence fills its audio.
            self.make(folder / 'intro.mp4', '320x180', 1, True)
            self.make(folder / 'body.mp4', '240x180', 2, False)
            seconds = intro.join(folder / 'intro.mp4', folder / 'body.mp4', folder / 'out.mp4')
            result = intro.probe(folder / 'out.mp4')
        self.assertAlmostEqual(seconds, 1, places=1)
        self.assertEqual((result['width'], result['height']), (240, 180))
        self.assertTrue(result['audio'])
        self.assertAlmostEqual(result['duration'], 3, delta=0.1)


if __name__ == '__main__':
    unittest.main()

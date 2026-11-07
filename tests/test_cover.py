import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'cover'))
sys.path.insert(0, str(ROOT / 'scripts'))
import production as cover
import shuyu


class CoverTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.source = self.base / 'film'
        self.source.mkdir()
        renders = self.base / 'output/renders'
        reports = self.base / 'output/reports'
        self.files = {'source': self.source, 'movie': renders / 'film.mp4',
                      'cover': renders / 'film-cover.jpg', 'thumbnail': reports / 'cover-mobile.jpg',
                      'report': reports / 'cover-check.json', 'delivery': self.base / 'output/delivery.json'}
        patcher = patch.object(cover, 'paths', return_value=self.files)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.spec = {'schema': 'shuyu-cover/v1', 'title': 'A smooth surface', 'size': [640, 360],
                     'mode': 'compose', 'image': 'base.png',
                     'provenance': {'kind': 'project-original', 'source': 'Test fixture', 'license': 'project-internal'},
                     'texts': [{'text': 'Smooth', 'fontSize': 60, 'box': [32, 90, 500, 110]}]}
        Image.new('RGB', (640, 360), '#f4f2ec').save(self.source / 'base.png')
        font = ROOT / 'node_modules/katex/dist/fonts/KaTeX_Main-Regular.ttf'
        if not font.is_file():
            self.skipTest('npm ci required for portable test font')
        for name, value in [('font_path', font), ('font_record', {'faceIndex': 0})]:
            p = patch.object(cover, name, return_value=value)
            p.start()
            self.addCleanup(p.stop)
        self.save()

    def save(self):
        (self.source / 'cover.json').write_text(json.dumps(self.spec), encoding='utf-8')

    def test_real_build_and_mobile_preview(self):
        cover.build('film')
        cover.check('film')
        with Image.open(self.files['cover']) as image:
            self.assertEqual(image.size, (640, 360))
            self.assertEqual(image.format, 'JPEG')
            # The title must produce visible pixels, not an empty background.
            self.assertLess(image.getextrema()[0][0], 100)
        with Image.open(self.files['thumbnail']) as image:
            self.assertEqual(image.width, 360)

    def test_missing_image_or_outside_image_is_rejected(self):
        for value in ['missing.png', '../outside.png']:
            self.spec['image'] = value
            self.save()
            with self.assertRaises(ValueError):
                cover.preflight('film')
        self.assertFalse(self.files['cover'].exists())

    def test_text_overflow_and_outside_boxes_fail_before_writing(self):
        for box in [[0, 0, 20, 20], [620, 20, 200, 100]]:
            self.spec['texts'][0]['box'] = box
            self.save()
            with self.assertRaises(ValueError):
                cover.build('film')
        self.assertFalse(self.files['cover'].exists())

    def test_input_or_output_changes_invalidate_cover(self):
        cover.build('film')
        self.spec['texts'][0]['text'] = 'Updated'
        self.save()
        with self.assertRaisesRegex(ValueError, 'inputs changed'):
            cover.check('film')
        cover.build('film')
        Image.new('RGB', (640, 360), 'black').save(self.source / 'base.png')
        with self.assertRaisesRegex(ValueError, 'inputs changed'):
            cover.check('film')
        cover.build('film')
        self.files['cover'].write_bytes(b'broken jpeg')
        with self.assertRaisesRegex(ValueError, 'differs'):
            cover.check('film')

    def test_ready_mode_does_not_silently_crop(self):
        self.spec.update(mode='ready', texts=[])
        self.save()
        Image.new('RGB', (640, 640), 'white').save(self.source / 'base.png')
        with self.assertRaisesRegex(ValueError, 'aspect ratio'):
            cover.build('film')
        self.spec['fit'] = 'cover'
        self.save()
        cover.build('film')
        cover.check('film')

    def test_delivery_needs_both_files_and_successful_measurement(self):
        cover.build('film')
        with self.assertRaisesRegex(ValueError, 'missing'):
            cover.package_delivery('film', {'ok': True})
        # Bytes stand in for a previously measured MP4; this test checks pairing only.
        self.files['movie'].write_bytes(b'measured video fixture')
        with self.assertRaisesRegex(ValueError, 'measurement failed'):
            cover.package_delivery('film', {'ok': False})
        cover.package_delivery('film', {'ok': True})
        cover.check_delivery('film')
        self.files['movie'].write_bytes(b'a newer video')
        with self.assertRaisesRegex(ValueError, 'video changed'):
            cover.check_delivery('film')
        self.files['movie'].unlink()
        with self.assertRaisesRegex(ValueError, 'missing'):
            cover.check_delivery('film')

    def test_rebuilt_cover_needs_new_delivery_manifest(self):
        cover.build('film')
        self.files['movie'].write_bytes(b'measured video fixture')
        cover.package_delivery('film', {'ok': True})
        self.spec['title'] = 'Updated metadata only'
        self.save()
        cover.build('film')
        with self.assertRaisesRegex(ValueError, 'earlier cover'):
            cover.check_delivery('film')

    def test_render_preflights_film_before_expensive_work(self):
        (self.source / 'cover.json').unlink()
        with patch.object(shuyu, 'python_path', return_value=Path('/not-installed/python')), \
             patch.object(shuyu, 'project_config', return_value={'source': 'films/test'}), \
             patch.object(shuyu, 'prepare_project') as prepare:
            with self.assertRaisesRegex(ValueError, 'Missing'):
                shuyu.main(['render', 'test'])
            prepare.assert_not_called()

    def test_brand_and_technical_examples_are_not_films(self):
        self.assertTrue(cover.required({'source': 'films/example'}))
        self.assertFalse(cover.required({'source': 'brand'}))
        self.assertFalse(cover.required({'source': 'examples/staircase'}))

    def test_render_packages_only_after_video_measurement_succeeds(self):
        import intro
        sys.path.insert(0, str(ROOT / 'sound'))
        import audio_state

        def output(project, *parts, create=False):
            path = self.base / 'output'
            path = path.joinpath(*parts)
            if create:
                path.mkdir(parents=True, exist_ok=True)
            return path

        self.files['movie'].parent.mkdir(parents=True, exist_ok=True)
        self.files['movie'].write_bytes(b'measured render fixture')
        for exit_code in (0, 1):
            def measurement(command, **kwargs):
                cover.write_json(Path(command[-1]), {'ok': exit_code == 0})
                return exit_code

            with patch.object(shuyu, 'python_path', return_value=Path('/not-installed/python')), \
                 patch.object(shuyu, 'project_config', return_value={'source': 'films/test', 'video': 'film.mp4'}), \
                 patch.object(shuyu, 'prepare_project', return_value=self.source), \
                 patch.object(shuyu, 'hyperframes_version', return_value='0.8.223'), \
                 patch.object(shuyu, 'output_dir', side_effect=output), \
                 patch.object(shuyu, 'invoke'), \
                 patch.object(shuyu.subprocess, 'call', side_effect=measurement), \
                 patch.object(audio_state, 'validate_mix_state'), \
                 patch.object(intro, 'wanted', return_value=False):
                self.assertEqual(shuyu.main(['render', 'film']), exit_code)
            if exit_code == 0:
                cover.check_delivery('film')
            else:
                self.assertFalse(self.files['delivery'].exists())


if __name__ == '__main__':
    unittest.main()

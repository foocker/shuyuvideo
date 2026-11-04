from pathlib import Path
import json
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'scripts/validation'))
import screen_text
import render_check
import shuyu

PAGE = '''<!doctype html><html><body><template><style>.a{{content:"\\frac"}}</style>
<div id="root" data-composition-id="main" data-width="1440" data-height="1080">
<div class="tag">{text}</div><span data-tex="{tex}"></span>
<div data-literal-text>34.2 × 46.9 cm</div></div>
<script>const label = '{script}'; const ease = 'power2.out'; tl.to('#a', {{x: 1}});</script>
</template></body></html>'''


def page(directory, text='长方形面积', tex='n(n+1)', script='一道台阶'):
    (directory / 'index.html').write_text(PAGE.format(text=text, tex=tex, script=script), encoding='utf-8')


class ScreenTextTests(unittest.TestCase):
    def scan(self, **kwargs):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            page(directory, **kwargs)
            return [f['rule'] for f in screen_text.scan(directory)]

    def test_clean_page_passes(self):
        # TeX in data-tex, CSS, selectors and marked literal text are not flagged.
        self.assertEqual(self.scan(), [])

    def test_production_traces_are_found(self):
        self.assertEqual(self.scan(text='面积??'), ['mojibake'])
        self.assertEqual(self.scan(text='面积是多少?'), ['mojibake'])
        self.assertEqual(self.scan(text='结果 \\frac{n}{2}'), ['bare-tex'])
        self.assertEqual(self.scan(text='面积 n²'), ['unicode-math'])
        self.assertEqual(self.scan(text='01 / 弯曲'), ['production-note'])
        self.assertEqual(self.scan(text='镜头3 台阶'), ['production-note'])
        self.assertEqual(self.scan(script='TODO 台阶'), ['production-note'])

    def test_chinese_in_tex_must_use_text(self):
        self.assertEqual(self.scan(tex='面积=n'), ['tex-cjk'])
        self.assertEqual(self.scan(tex='\\text{面积}=n'), [])


class RenderCheckTests(unittest.TestCase):
    def probe(self, audio=True, audio_duration=10.0, size=(1440, 1080)):
        streams = [{'codec_type': 'video', 'width': size[0], 'height': size[1],
                    'avg_frame_rate': '30/1', 'duration': '10.0'}]
        if audio:
            streams.append({'codec_type': 'audio', 'duration': str(audio_duration)})
        return {'streams': streams, 'format': {'duration': '10.0'}}

    def run_check(self, project_files=(), loud=-16.0, **probe):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            page(directory)
            for name in project_files:
                (directory / name).parent.mkdir(parents=True, exist_ok=True)
                (directory / name).write_bytes(b'x')
            measured = {'integratedLufs': loud, 'truePeakDbtp': -3.0, 'lra': 4.0}
            with patch.object(render_check, 'probe', return_value=self.probe(**probe)), \
                 patch.object(render_check, 'loudness', return_value=measured):
                return render_check.check(Path('film.mp4'), directory)

    def test_canvas_size_comes_from_root_composition(self):
        errors, summary = self.run_check()
        self.assertEqual(errors, [])
        self.assertEqual((summary['width'], summary['height']), (1440, 1080))
        errors, _ = self.run_check(size=(1920, 1080))
        self.assertIn('resolution', errors[0])

    def test_missing_soundtrack_and_drift_fail(self):
        errors, _ = self.run_check(project_files=['assets/audio/final-mix.wav'], audio=False)
        self.assertIn('no audio stream', errors[0])
        errors, _ = self.run_check(audio_duration=9.5)
        self.assertIn('differ', errors[0])

    def test_loudness_is_enforced_only_for_mastered_projects(self):
        errors, summary = self.run_check(loud=-24.0)
        self.assertEqual(errors, [])
        self.assertTrue(summary['warnings'])
        errors, _ = self.run_check(project_files=['assets/audio/mix-report.json'], loud=-24.0)
        self.assertTrue(errors)


class PrepareSyncTests(unittest.TestCase):
    def test_deleted_source_files_leave_the_build_but_generated_files_stay(self):
        ignore = shutil.ignore_patterns('renders')
        with tempfile.TemporaryDirectory(dir=ROOT / 'output') as tmp:
            source, build = Path(tmp) / 'source', Path(tmp) / 'build'
            (source / 'compositions').mkdir(parents=True)
            for name in ('index.html', 'compositions/old.html', 'compositions/keep.html'):
                (source / name).write_text(name, encoding='utf-8')
            build.mkdir()
            shuyu.remove_deleted_sources(source, build, ignore)
            shutil.copytree(source, build, dirs_exist_ok=True, ignore=ignore)
            (build / 'assets/voice').mkdir(parents=True)
            (build / 'assets/voice/q1.mp3').write_bytes(b'take')
            (source / 'compositions/old.html').rename(source / 'compositions/new.html')
            shuyu.remove_deleted_sources(source, build, ignore)
            shutil.copytree(source, build, dirs_exist_ok=True, ignore=ignore)
            self.assertFalse((build / 'compositions/old.html').exists())
            self.assertTrue((build / 'compositions/new.html').exists())
            self.assertTrue((build / 'assets/voice/q1.mp3').exists())
            files = json.loads((build / shuyu.SOURCE_MANIFEST).read_text(encoding='utf-8'))['files']
            self.assertIn('compositions/new.html', files)


import accumulation

METHODS_SAMPLE = '''## M01 · 同一对象返回

## M02 · 缩小再恢复范围
'''


def with_methods(test):
    """Run a test against a two-method library, independent of the local studies/."""
    def run(self):
        with tempfile.TemporaryDirectory() as tmp:
            methods = Path(tmp) / 'methods.md'
            methods.write_text(METHODS_SAMPLE, encoding='utf-8')
            with patch.object(accumulation, 'METHODS', methods):
                test(self)
    run.__name__ = test.__name__
    return run


class AccumulationTests(unittest.TestCase):
    @with_methods
    def test_register_and_example_retro_are_valid(self):
        self.assertEqual(accumulation.check_defects(), [])
        example = accumulation.load(ROOT / 'docs/retro.example.json')
        self.assertEqual(accumulation.check_retro(example), [])

    def test_guarded_defect_needs_an_existing_check(self):
        register = {'schema': 'shuyu-defects/v1', 'defects': [
            {'id': 'X1', 'symptom': 's', 'cause': 'c', 'status': 'guarded', 'check': ''},
            {'id': 'X2', 'symptom': 's', 'cause': 'c', 'status': 'guarded', 'check': 'scripts/missing.py'}]}
        errors = accumulation.check_defects(register)
        self.assertTrue(any('X1' in e for e in errors) and any('X2' in e for e in errors))

    @with_methods
    def test_retro_rejects_unknown_ids_and_times_outside_the_film(self):
        retro = {'schema': 'shuyu-retro/v1', 'project': 'p', 'date': '2026-11-04', 'duration': 10,
                 'methods': [{'id': 'M99', 'at': [8, 12], 'purpose': 'x', 'outcome': 'maybe'}],
                 'defects': [{'id': 'D99'}]}
        errors = ' '.join(accumulation.check_retro(retro))
        for text in ('unknown method', 'outcome', 'inside the film', 'D99', 'fix'):
            self.assertIn(text, errors)

    @with_methods
    def test_summary_counts_outcomes_per_method(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for name, outcome in (('a', 'worked'), ('b', 'failed')):
                path = Path(tmp) / f'{name}.json'
                path.write_text(json.dumps({'project': name, 'methods': [
                    {'id': 'M01', 'at': [0, 1], 'purpose': 'x', 'outcome': outcome}]}), encoding='utf-8')
                paths.append(path)
            result = accumulation.summary(paths)
        self.assertEqual(result['methods']['M01']['uses'], 2)
        self.assertEqual(result['methods']['M01']['projects'], ['a', 'b'])
        self.assertEqual((result['methods']['M01']['worked'], result['methods']['M01']['failed']), (1, 1))
        self.assertIn('M02', result['unused'])

    def test_retro_without_the_local_research_library_checks_id_format_only(self):
        retro = {'schema': 'shuyu-retro/v1', 'project': 'p', 'date': '2026-11-04', 'duration': 10,
                 'methods': [{'id': 'M42', 'at': [1, 2], 'purpose': 'x', 'outcome': 'worked'},
                             {'id': 'move', 'at': [1, 2], 'purpose': 'x', 'outcome': 'worked'}]}
        with patch.object(accumulation, 'METHODS', ROOT / 'missing/methods.md'):
            errors = accumulation.check_retro(retro)
            self.assertIsNone(accumulation.summary([])['unused'])
        self.assertEqual(len(errors), 1)
        self.assertIn('look like M01', errors[0])

    def test_reuse_reports_every_shared_runtime(self):
        modules = accumulation.reuse()
        self.assertIn('motion/runtime/camera.js', modules)
        for record in modules.values():
            self.assertEqual(record['proven'], len(record['works']) >= 2)
            self.assertTrue(all(not w.startswith('examples/') for w in record['works']))


if __name__ == '__main__':
    unittest.main()

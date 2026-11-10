import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'sound'))
from audio_state import validate_mix_state
SPEC = importlib.util.spec_from_file_location('sound_mix', ROOT / 'sound/mix.py')
mix = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mix)


class PlacementTests(unittest.TestCase):
    def test_negative_start_trims_source_and_keeps_peak_on_clock(self):
        data = np.zeros((12, 2), dtype=np.float32)
        data[8] = [1, .5]
        track = np.zeros((20, 2), dtype=np.float32)
        mix.place(track, data, -5 / mix.SR)
        self.assertEqual(np.argmax(track[:, 0]), 3)
        np.testing.assert_array_equal(track[:7], data[5:])

    def test_end_trim_and_overlapping_samples(self):
        track = np.ones((5, 2), dtype=np.float32)
        mix.place(track, np.full((4, 2), 2), 3 / mix.SR)
        np.testing.assert_array_equal(track[:, 0], [1, 1, 1, 3, 3])

    def test_fully_outside_film_is_silent(self):
        for offset in (-10, 5, 10):
            with self.subTest(offset=offset):
                track = np.zeros((5, 2))
                mix.place(track, np.ones((5, 2)), offset / mix.SR)
                self.assertFalse(track.any())


class LoudnessTests(unittest.TestCase):
    def test_acceptance_bounds(self):
        for level in (-17, -16, -15):
            self.assertTrue(mix.validate_loudness({'integratedLufs': level, 'truePeakDbtp': -1.5, 'lra': 3})['passed'])
        for level, peak in [(-17.1, -3), (-14.9, -3), (-16, -1.4), (-float('inf'), -float('inf')), (float('nan'), -3)]:
            with self.subTest(level=level, peak=peak):
                self.assertFalse(mix.validate_loudness({'integratedLufs': level, 'truePeakDbtp': peak, 'lra': 0})['passed'])

    def test_failed_ffmpeg_measurement_is_not_accepted(self):
        run = subprocess.CompletedProcess([], 1, '', 'decoder failed')
        with patch.object(mix.subprocess, 'run', return_value=run):
            with self.assertRaisesRegex(RuntimeError, 'decoder failed'):
                mix.loudness(Path('broken.wav'))


@unittest.skipUnless(shutil.which('ffmpeg'), 'FFmpeg is required for real audio regression tests')
class MixingIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='shuyu-mix-test-')
        self.addCleanup(self.temp.cleanup)
        self.film = Path(self.temp.name)
        self.audio = self.film / 'assets/audio'
        self.audio.mkdir(parents=True)
        (self.film / 'voice-timings.json').write_text(json.dumps({'duration': 4, 'lines': []}), encoding='utf-8')
        (self.film / 'narration.json').write_text('{"bedGain": 1}', encoding='utf-8')

    def run_mix(self):
        return subprocess.run([sys.executable, str(ROOT / 'sound/mix.py'), str(self.film)],
                              capture_output=True, text=True, encoding='utf-8', timeout=30)

    def report(self):
        text = (self.audio / 'mix-report.json').read_text(encoding='utf-8')
        self.assertNotIn('Infinity', text)
        self.assertNotIn('NaN', text)
        return json.loads(text)

    def test_silence_fails_without_replacing_previous_tracks(self):
        for name in ('narration.wav', 'sound-effects.wav', 'final-mix.wav'):
            (self.audio / name).write_bytes(b'previous accepted output')
        run = self.run_mix()
        self.assertEqual(run.returncode, 1, run.stderr)
        report = self.report()
        self.assertEqual(report['status'], 'failed')
        self.assertFalse(report['outputsPublished'])
        self.assertIsNone(report['measured']['integratedLufs'])
        for name in ('narration.wav', 'sound-effects.wav', 'final-mix.wav'):
            self.assertEqual((self.audio / name).read_bytes(), b'previous accepted output')
        self.assertFalse(list(self.audio.glob('.mix-*')))

    def test_real_audio_passes_and_stems_match_master(self):
        t = np.arange(4 * mix.SR) / mix.SR
        signal = (.05 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
        sf.write(self.audio / 'bed.wav', np.column_stack([signal, signal]), mix.SR, subtype='FLOAT')
        run = self.run_mix()
        self.assertEqual(run.returncode, 0, run.stderr)
        report = self.report()
        self.assertTrue(report['outputsPublished'])
        self.assertTrue(report['validation']['passed'])
        self.assertEqual(report['status'], 'passed')
        validate_mix_state(self.film)
        self.assertTrue(mix.validate_loudness(mix.loudness(self.audio / 'final-mix.wav'))['passed'])
        final, rate = sf.read(self.audio / 'final-mix.wav', always_2d=True)
        voice, _ = sf.read(self.audio / 'narration.wav', always_2d=True)
        effects, _ = sf.read(self.audio / 'sound-effects.wav', always_2d=True)
        self.assertEqual(rate, 48000)
        self.assertEqual(len(final), 4 * mix.SR)
        self.assertEqual(report['lines'], 0)
        self.assertFalse(voice.any())
        np.testing.assert_allclose(final, voice + effects, atol=2 / 32768)

    def test_shot_clock_and_music_need_no_narration_config_or_tts_cache(self):
        (self.film / 'narration.json').unlink()
        t = np.arange(4 * mix.SR) / mix.SR
        signal = (.05 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
        sf.write(self.audio / 'bed.wav', np.column_stack([signal, signal]), mix.SR, subtype='FLOAT')
        run = self.run_mix()
        self.assertEqual(run.returncode, 0, run.stderr)
        validate_mix_state(self.film)
        report = self.report()
        self.assertEqual((report['duration'], report['lines']), (4, 0))
        self.assertNotIn('narration.json', report['inputs'])
        self.assertFalse((self.film / 'assets/voice').exists())
        voice, _ = sf.read(self.audio / 'narration.wav', always_2d=True)
        self.assertEqual(len(voice), 4 * mix.SR)
        self.assertFalse(voice.any())

    def test_failed_report_cannot_validate_an_existing_accepted_mix(self):
        (self.audio / 'final-mix.wav').write_bytes(b'old accepted track')
        (self.audio / 'mix-report.json').write_text(json.dumps({'status': 'failed', 'outputsPublished': False}), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'did not pass'):
            validate_mix_state(self.film)

    def test_peak_limited_quiet_mix_is_rejected(self):
        # A quiet continuous bed plus one large transient cannot reach the
        # target by gain alone without violating the true-peak ceiling.
        t = np.arange(4 * mix.SR) / mix.SR
        signal = (.002 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
        signal[2 * mix.SR] = 1
        sf.write(self.audio / 'bed.wav', np.column_stack([signal, signal]), mix.SR, subtype='FLOAT')
        run = self.run_mix()
        self.assertEqual(run.returncode, 1, run.stderr)
        report = self.report()
        self.assertFalse(report['validation']['passed'])
        self.assertLess(report['measured']['integratedLufs'], -17)
        self.assertFalse((self.audio / 'final-mix.wav').exists())


if __name__ == '__main__':
    unittest.main()

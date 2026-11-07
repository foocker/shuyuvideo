import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'sound'))
from audio_state import file_hash, input_state, validate_mix_state


class AudioStateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.film = Path(self.tmp.name)
        self.config = {'voice': 'test-voice', 'rate': '+0%', 'lines': [{'id': 'q1', 'text': '新稿'}]}
        self.clock = {'voice': 'test-voice', 'duration': 4, 'lines': [
            {'id': 'q1', 'text': '新稿', 'file': 'assets/voice/q1.mp3', 'start': .5, 'end': 3.5}]}
        self.write('narration.json', self.config)
        self.write('voice-timings.json', self.clock)
        self.write('sound-cues.json', [])
        self.write_take('新稿')
        (self.film / 'assets/voice/q1.mp3').write_bytes(b'recorded audio')
        (self.film / 'assets/audio').mkdir()

    def write(self, name, obj):
        path = self.film / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj, ensure_ascii=False), encoding='utf-8')

    def write_take(self, text, rate=None):
        key = [text, self.config['voice'], rate or self.config['rate']]
        self.write('assets/voice/q1.json', {'text': text, 'duration': 3,
            'fingerprint': hashlib.sha256(json.dumps(key, ensure_ascii=False).encode()).hexdigest()})

    def accept(self):
        output = self.film / 'assets/audio/final-mix.wav'
        output.write_bytes(b'accepted audio')
        self.write('assets/audio/mix-report.json', {'status': 'passed', 'outputsPublished': True,
            'duration': 4, 'inputs': input_state(self.film), 'outputSha256': {'final-mix.wav': file_hash(output)}})

    def test_source_copy_of_old_voice_is_rejected(self):
        self.write_take('旧稿')
        with self.assertRaisesRegex(ValueError, 'Stale voice cache'):
            input_state(self.film)

    def test_old_clock_and_changed_take_length_are_rejected(self):
        self.clock['lines'][0]['text'] = '旧稿'
        self.write('voice-timings.json', self.clock)
        with self.assertRaisesRegex(ValueError, 'disagree'):
            input_state(self.film)
        self.clock['lines'][0].update(text='新稿', end=3)
        self.write('voice-timings.json', self.clock)
        with self.assertRaisesRegex(ValueError, 'duration changed'):
            input_state(self.film)

    def test_same_duration_edits_require_remixing(self):
        self.accept()
        validate_mix_state(self.film)
        self.config['lines'][0]['text'] = '改稿'
        self.clock['lines'][0]['text'] = '改稿'
        self.write('narration.json', self.config)
        self.write('voice-timings.json', self.clock)
        self.write_take('改稿')
        with self.assertRaisesRegex(ValueError, 'inputs changed'):
            validate_mix_state(self.film)

    def test_replaced_audio_and_changed_bed_are_rejected(self):
        self.accept()
        (self.film / 'assets/audio/final-mix.wav').write_bytes(b'old source mix')
        with self.assertRaisesRegex(ValueError, 'Mastered audio changed'):
            validate_mix_state(self.film)
        self.accept()
        (self.film / 'assets/audio/bed.wav').write_bytes(b'new music')
        with self.assertRaisesRegex(ValueError, 'inputs changed'):
            validate_mix_state(self.film)

    def test_old_passed_report_checks_current_duration(self):
        self.write('assets/audio/mix-report.json', {'status': 'passed', 'outputsPublished': True, 'duration': 4})
        validate_mix_state(self.film)
        self.clock['duration'] = 5
        self.write('voice-timings.json', self.clock)
        with self.assertRaisesRegex(ValueError, 'Mix duration differs'):
            validate_mix_state(self.film)

    def test_unused_cached_files_do_not_invalidate_mix(self):
        self.accept()
        self.write('assets/voice/deleted-line.json', {'text': 'unused'})
        validate_mix_state(self.film)

    def test_line_rate_change_requires_new_take_and_mix(self):
        self.accept()
        self.config['lines'][0]['rate'] = '+8%'
        self.write('narration.json', self.config)
        with self.assertRaisesRegex(ValueError, 'Stale voice cache'):
            input_state(self.film)
        self.write_take('新稿', '+8%')
        input_state(self.film)
        with self.assertRaisesRegex(ValueError, 'inputs changed'):
            validate_mix_state(self.film)
        self.accept()
        validate_mix_state(self.film)

    def test_incomplete_or_malformed_reports_are_rejected(self):
        for report in ([], {'status': 'passed', 'outputsPublished': True, 'duration': None},
                       {'status': 'passed', 'outputsPublished': True, 'inputs': {}}):
            with self.subTest(report=report):
                self.write('assets/audio/mix-report.json', report)
                with self.assertRaises(ValueError):
                    validate_mix_state(self.film)


if __name__ == '__main__':
    unittest.main()

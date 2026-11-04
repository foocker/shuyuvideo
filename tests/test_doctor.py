import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('environment_doctor', ROOT / 'scripts/doctor.py')
doctor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(doctor)


class DoctorTests(unittest.TestCase):
    def test_old_tts_version_is_detected(self):
        with patch.object(doctor.importlib.metadata, 'version', return_value='7.2.8'), \
             patch.object(doctor.importlib, 'import_module'):
            checks = doctor.python_checks(audio_only=True)
        tts = next(c for c in checks if c['name'] == 'edge-tts')
        self.assertEqual(tts['status'], 'fail')
        self.assertIn('pip install -r', tts['fix'])

    def test_missing_dependency_has_fix(self):
        with patch.object(doctor.importlib.metadata, 'version', side_effect=doctor.importlib.metadata.PackageNotFoundError('missing')):
            checks = doctor.python_checks(audio_only=True)
        self.assertTrue(all(c['status'] == 'fail' and c['fix'] for c in checks if c['name'] != 'Python'))

    def test_project_pin_is_used_and_conflicts_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / 'package.json'
            package.write_text(json.dumps({'scripts': {'render': 'npx --yes hyperframes@0.8.220 render'}}), encoding='utf-8')
            self.assertEqual(doctor.hyperframes_version(root), '0.8.220')
            package.write_text(json.dumps({'scripts': {'render': 'npx hyperframes@0.8.220 render', 'check': 'npx hyperframes@0.8.223 check'}}), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Conflicting'):
                doctor.hyperframes_version(root)

    def test_hyperframes_json_failure_blocks_even_with_zero_process_exit(self):
        checks = doctor.classify_hyperframes({'ok': False, 'checks': [
            {'name': 'Chrome', 'ok': False, 'detail': 'Missing browser'},
            {'name': 'Docker running', 'ok': False, 'detail': 'Not running'}]}, '0.8.223')
        self.assertEqual(checks[0]['status'], 'fail')
        self.assertIn('browser ensure', checks[0]['fix'])
        self.assertEqual(checks[1]['status'], 'warn')

    def test_optional_tools_do_not_block_local_render(self):
        checks = doctor.classify_hyperframes({'ok': False, 'checks': [
            {'name': 'Chrome', 'ok': True}, {'name': 'TTS (Kokoro)', 'ok': False},
            {'name': 'Version', 'ok': False, 'detail': '0.8.223 -> 0.9.10 available'}]}, '0.8.223')
        self.assertFalse(any(c['status'] == 'fail' for c in checks))

    def test_cli_failure_has_nonzero_exit_and_json(self):
        failure = doctor.result('edge-tts', False, '7.2.8', 'install supported version')
        with patch.object(doctor, 'python_checks', return_value=[failure]), \
             patch.object(doctor, 'executable_check', return_value=doctor.result('ffmpeg', True, 'available')), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            code = doctor.main(['--audio-only', '--json'])
        self.assertEqual(code, 1)
        self.assertFalse(json.loads(output.getvalue())['ok'])


if __name__ == '__main__':
    unittest.main()

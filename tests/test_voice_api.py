import asyncio
import base64
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
import wave

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'sound'))
import voice
import voice_api as api
from voice_config import voice_fingerprint, restore_word_texts
from voice_roles import read_env, resolve_role, credentials
from audio_state import validate_voice

SECRET = 'test-secret-never-persist'
ENV = {'DOUBAO_API_KEY': SECRET, 'MINIMAX_API_KEY': SECRET}


def sse(*events):
    return io.BytesIO(''.join('event: 352\ndata: ' + json.dumps(e, ensure_ascii=False) + '\n\n'
                            for e in events).encode('utf-8'))


class RoleTests(unittest.TestCase):
    def test_env_is_literal_and_os_precedence_is_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / '.env'
            path.write_text('\ufeff# local\nA="$(do not execute)"\nB=local # comment\nC=key#literal\n', encoding='utf-8')
            self.assertEqual(read_env(path, {'B': 'os'}),
                             {'A': '$(do not execute)', 'B': 'os', 'C': 'key#literal'})
            path.write_text('SECRET="unclosed', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'line 1: unmatched quote'):
                read_env(path, {})

    def test_default_is_manuscript_voice_and_legacy_fingerprint(self):
        line, config = {'text': '原声'}, {'voice': 'zh-CN-YunxiNeural', 'rate': '+10%'}
        profile = resolve_role(config, env={})
        expected = hashlib.sha256(json.dumps(['原声', config['voice'], '+10%'], ensure_ascii=False).encode()).hexdigest()
        self.assertEqual(profile['provider'], 'edge')
        self.assertEqual(voice_fingerprint(line, config, profile), expected)
        self.assertEqual(credentials(profile, {}), {})

    def test_custom_roles_and_api_identity_exclude_keys(self):
        config, line = {'voice': 'old'}, {'text': '旋转'}
        profile = resolve_role(config, 'minimax-custom', {**ENV, 'MINIMAX_VOICE_ID': 'my-clone'})
        self.assertEqual(profile['voice'], 'my-clone')
        self.assertNotIn(SECRET, json.dumps(profile))
        original = voice_fingerprint(line, config, profile)
        self.assertEqual(original, voice_fingerprint(line, {'voice': 'different-unused-edge'}, profile))
        for field, value in [('voice', 'new-clone'), ('model', 'speech-2.8-turbo'), ('sample_rate', 24000)]:
            self.assertNotEqual(original, voice_fingerprint(line, config, {**profile, field: value}))
        with self.assertRaisesRegex(ValueError, 'MINIMAX_VOICE_ID'):
            resolve_role(config, 'minimax-custom', {})

    def test_doubao_auth_and_resource(self):
        profile = resolve_role({}, 'doubao-magnetic', ENV)
        self.assertEqual(credentials(profile, ENV), {'X-Api-Key': SECRET})
        self.assertEqual(credentials(profile, {'DOUBAO_APP_ID': 'id', 'DOUBAO_ACCESS_TOKEN': SECRET}),
                         {'X-Api-App-Id': 'id', 'X-Api-Access-Key': SECRET})
        with self.assertRaisesRegex(ValueError, 'credentials'):
            credentials(profile, {})
        with self.assertRaisesRegex(ValueError, '2.0 resource'):
            resolve_role({}, 'doubao-magnetic', {'DOUBAO_RESOURCE_ID': 'seed-tts-1.0'})
        with self.assertRaisesRegex(ValueError, 'HTTPS'):
            resolve_role({}, 'minimax-gentle', {'MINIMAX_TTS_URL': 'https://host/path?api_key=secret'})


class ProtocolTests(unittest.TestCase):
    def test_request_contracts_use_word_subtitles_and_native_rates(self):
        for role in ('doubao-magnetic', 'minimax-gentle'):
            profile = resolve_role({}, role, ENV)
            req = api.request_spec('五重旋转。', '+10%', profile, ENV)
            data = json.loads(req.data)
            self.assertNotIn(SECRET, req.data.decode())
            if role.startswith('doubao'):
                params = data['req_params']['audio_params']
                self.assertEqual(params['speech_rate'], 10)
                self.assertTrue(params['enable_subtitle'])
                self.assertNotIn('enable_timestamp', params)
                self.assertEqual(req.get_header('X-api-key'), SECRET)
            else:
                self.assertEqual(data['voice_setting']['speed'], 1.1)
                self.assertEqual(data['subtitle_type'], 'word')
                self.assertEqual(data['audio_setting']['sample_rate'], 44100)
                self.assertEqual(req.get_header('Authorization'), 'Bearer ' + SECRET)
        with self.assertRaises(ValueError):
            api.rate_percent('+101%')

    def test_doubao_orders_late_subtitle_events_without_changing_times(self):
        pcm = b'\0\0' * 24000
        events = sse({'code': 0, 'data': base64.b64encode(pcm).decode()},
                     {'code': 0, 'sentence': {'words': [{'word': '后。', 'startTime': .6, 'endTime': .8}]}},
                     {'code': 0, 'sentence': {'words': [{'word': '前', 'startTime': .1, 'endTime': .3}]}},
                     {'code': 20000000})
        audio, words = api.parse_doubao(events)
        checked = api.validate_words(words, '前后。', 1)
        self.assertEqual(audio, pcm)
        self.assertEqual([w['start'] for w in checked], [.1, .6])

    def test_doubao_requires_terminal_success_and_sanitizes_errors(self):
        with self.assertRaisesRegex(api.VoiceAPIError, 'terminal success'):
            api.parse_doubao(sse({'code': 0, 'data': None}))
        with self.assertRaises(api.VoiceAPIError) as caught:
            api.parse_doubao(sse({'code': 45000000, 'message': SECRET}))
        self.assertNotIn(SECRET, str(caught.exception))

    def test_minimax_native_ms_and_missing_word_subtitles(self):
        payload = {'base_resp': {'status_code': 0}, 'data': {
            'audio': '00000000', 'subtitle_file': 'https://example.com/subtitles?signature=test'}}
        segments = [{'text': '前后', 'timestamped_words': [
            {'word': '前', 'word_begin': 0, 'word_end': 1, 'time_begin': 120, 'time_end': 300},
            {'word': '后', 'word_begin': 1, 'word_end': 2, 'time_begin': 510, 'time_end': 800}]}]
        audio, words = api.parse_minimax(payload, lambda url: segments)
        self.assertEqual(audio, b'\0\0\0\0')
        self.assertEqual(words[1]['start'], .51)
        _, absent = api.parse_minimax(payload, lambda url: [{'text': '前后', 'time_begin': 0, 'time_end': 800}])
        with self.assertRaisesRegex(api.VoiceAPIError, 'no word timestamps'):
            api.validate_words(absent, '前后', 1)
        with self.assertRaises(api.VoiceAPIError) as caught:
            api.parse_minimax({'base_resp': {'status_code': 1004, 'status_msg': SECRET}}, lambda url: [])
        self.assertNotIn(SECRET, str(caught.exception))

    def test_partial_and_invalid_words_fail_without_invented_timings(self):
        for words in ([{'text': '前', 'start': 0, 'end': .2}],
                      [{'text': '前后', 'start': 0, 'end': 4}],
                      [{'text': '前后', 'start': float('nan'), 'end': .2}]):
            with self.assertRaises(api.VoiceAPIError):
                api.validate_words(words, '前后', 1)
        restored = restore_word_texts([{'text': '五崇，旋转。', 'start': .1, 'end': 1}],
                                      '五崇旋转。', '五重旋转。')
        self.assertEqual(restored[0]['text'], '五重旋转')
        self.assertEqual(restored[0]['start'], .1)

    def test_http_errors_never_show_raw_details_or_secret(self):
        for exc in (HTTPError('https://example.com?secret=' + SECRET, 401, SECRET, {}, None), URLError(SECRET)):
            with patch.object(api, 'urlopen', side_effect=exc), self.assertRaises(api.VoiceAPIError) as caught:
                api.open_request(api.Request('https://example.com'))
            self.assertNotIn(SECRET, str(caught.exception))

    def test_authenticated_posts_disable_redirects(self):
        profile = resolve_role({}, 'minimax-gentle', ENV)
        request = api.request_spec('测试', '+0%', profile, ENV)
        with patch.object(api, 'build_opener') as builder:
            api.open_request(request)
            self.assertIsInstance(builder.call_args.args[0], api.NoAuthRedirect)
            self.assertIsNone(builder.call_args.args[0].redirect_request(
                request, None, 302, 'moved', {}, 'https://another-host.example'))

    def test_real_wav_adapter_with_mock_sse_and_no_auth_forwarding_to_subtitles(self):
        profile = resolve_role({}, 'doubao-magnetic', ENV)
        events = sse({'code': 0, 'data': base64.b64encode(b'\0\0' * 24000).decode()},
                     {'code': 0, 'sentence': {'words': [{'word': '旋转。', 'startTime': .1, 'endTime': .8}]}},
                     {'code': 20000000})
        with tempfile.TemporaryDirectory() as tmp, patch.object(api, 'open_request', return_value=events):
            dest = Path(tmp) / 'take.wav'
            words = api.synthesize_api('旋转。', '+10%', profile, ENV, dest)
            with wave.open(str(dest)) as audio:
                self.assertEqual((audio.getnframes(), audio.getframerate(), audio.getsampwidth()), (24000, 24000, 2))
            self.assertEqual(words[0]['start'], .1)
        with patch.object(api, 'open_request', return_value=io.BytesIO(b'[]')) as opener:
            api.download_subtitles('https://example.com/signed?token=123')
            self.assertNotIn('Authorization', opener.call_args.args[0].headers)
            self.assertNotIn('X-api-key', opener.call_args.args[0].headers)

    def test_minimax_wav_download_and_malformed_reply(self):
        profile = resolve_role({}, 'minimax-gentle', ENV)
        payload = {'base_resp': {'status_code': 0}, 'data': {
            'audio': (b'\0\0' * 44100).hex(), 'subtitle_file': 'https://example.com/subtitles'}}
        subtitles = [{'text': '旋转。', 'timestamped_words': [
            {'word': '旋转。', 'time_begin': 100, 'time_end': 800}]}]
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'take.wav'
            with patch.object(api, 'open_request', side_effect=[
                    io.BytesIO(json.dumps(payload).encode()), io.BytesIO(json.dumps(subtitles).encode())]):
                words = api.synthesize_api('旋转。', '+10%', profile, ENV, dest)
            with wave.open(str(dest)) as audio:
                self.assertEqual((audio.getnframes(), audio.getframerate()), (44100, 44100))
            self.assertEqual(words[0]['start'], .1)
            accepted = dest.read_bytes()
            for response in (b'not-json', b'[]', b'{"base_resp":0}'):
                with patch.object(api, 'open_request', return_value=io.BytesIO(response)), \
                        self.assertRaises(api.VoiceAPIError):
                    api.synthesize_api('旋转。', '+10%', profile, ENV, dest)
                self.assertEqual(dest.read_bytes(), accepted)


class PipelineTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.film = Path(tmp.name)
        self.config = {'voice': 'zh-CN-YunxiNeural', 'rate': '+10%', 'lines': [
            {'id': 'a', 'text': '前'}, {'id': 'b', 'text': '后', 'rate': '+8%'}]}
        (self.film / 'narration.json').write_text(json.dumps(self.config), encoding='utf-8')

    @staticmethod
    def generate(text, rate, profile, env, dest):
        with wave.open(str(dest), 'wb') as fp:
            fp.setnchannels(1)
            fp.setsampwidth(2)
            fp.setframerate(24000)
            fp.writeframes(b'\0\0' * 24000)
        return [{'text': text, 'start': .1, 'end': .8}]

    def test_role_sample_then_complete_then_cached_run_and_frozen_validation(self):
        settings = {**ENV, 'SHUYU_VOICE_ROLE': 'doubao-magnetic'}
        clock = self.film / 'voice-timings.json'
        clock.write_text('original clock')
        with patch.object(voice, 'read_env', return_value=settings), \
                patch.object(voice, 'synthesize_api', side_effect=self.generate) as generate, redirect_stdout(io.StringIO()):
            asyncio.run(voice.main(self.film, {'a'}, sample=True))
            self.assertEqual(clock.read_text(), 'original clock')
            asyncio.run(voice.main(self.film, set()))
            self.assertEqual(generate.call_count, 2)
            result = json.loads(clock.read_text())
            self.assertTrue(all(row['file'].endswith('.wav') for row in result['lines']))
            validate_voice(self.film, result)
            asyncio.run(voice.main(self.film, set()))
            self.assertEqual(generate.call_count, 2)
        with patch.dict('os.environ', {'SHUYU_VOICE_ROLE': 'minimax-gentle', 'DOUBAO_API_KEY': 'changed'}):
            validate_voice(self.film, result)
        for path in self.film.rglob('*.json'):
            self.assertNotIn(SECRET, path.read_text())
        changed = {**result, 'voiceProfile': {**result['voiceProfile'], 'voice': 'different'}}
        with self.assertRaisesRegex(ValueError, 'role changed'):
            validate_voice(self.film, changed)

    def test_failure_and_partial_role_change_preserve_existing_film(self):
        clock = self.film / 'voice-timings.json'
        clock.write_text('accepted clock')
        with patch.object(voice, 'read_env', return_value=ENV), \
                patch.object(voice, 'synthesize_api', side_effect=api.VoiceAPIError('failed')) as generate:
            with self.assertRaisesRegex(ValueError, 'Other lines'):
                asyncio.run(voice.main(self.film, {'a'}, 'minimax-gentle'))
            generate.assert_not_called()
            with self.assertRaises(api.VoiceAPIError):
                asyncio.run(voice.main(self.film, {'a'}, 'minimax-gentle', sample=True))
            self.assertEqual(generate.call_count, 1)
            generate.reset_mock()
            with self.assertRaises(api.VoiceAPIError):
                asyncio.run(voice.main(self.film, set(), 'minimax-gentle'))
            self.assertEqual(generate.call_count, 1)  # do not start the next paid request
        self.assertEqual(clock.read_text(), 'accepted clock')
        self.assertFalse(list(self.film.rglob('*.wav')))

    def test_dry_run_and_missing_credentials_never_request_network(self):
        with patch.object(voice, 'read_env', return_value={}), \
                patch.object(voice, 'synthesize_api') as generate, redirect_stdout(io.StringIO()) as output:
            asyncio.run(voice.main(self.film, set(), 'minimax-gentle', dry_run=True))
            self.assertFalse(json.loads(output.getvalue())['credentialsReady'])
            with self.assertRaisesRegex(ValueError, 'credentials'):
                asyncio.run(voice.main(self.film, set(), 'minimax-gentle'))
            generate.assert_not_called()
        self.assertFalse((self.film / 'assets').exists())


if __name__ == '__main__':
    unittest.main()

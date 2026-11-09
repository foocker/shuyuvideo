import asyncio
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'sound'))
import voice
from voice_config import effective_speech_text, restore_word_texts, voice_fingerprint


class VoiceRateTests(unittest.TestCase):
    def test_provider_and_cache_use_each_lines_effective_rate(self):
        class Request:
            async def stream(self):
                yield {'type': 'audio', 'data': b'test-audio'}
                yield {'type': 'WordBoundary', 'text': '回顾', 'offset': 1000000, 'duration': 2000000}

        async def exercise(folder, provider):
            config = {'voice': 'test', 'rate': '-3%'}
            regular = {'id': 'regular', 'text': '定义'}
            fast = {'id': 'fast', 'text': '回顾', 'rate': '+8%'}
            await voice.synthesize(regular, config, folder)
            await voice.synthesize(fast, config, folder)
            self.assertEqual([c.kwargs['rate'] for c in provider.call_args_list], ['-3%', '+8%'])
            await voice.synthesize(regular, config, folder)
            await voice.synthesize(fast, config, folder)
            self.assertEqual(provider.call_count, 2)
            fast['rate'] = '+6%'
            await voice.synthesize(fast, config, folder)
            await voice.synthesize(regular, config, folder)
            self.assertEqual(provider.call_count, 3)
            self.assertEqual(provider.call_args.kwargs['rate'], '+6%')
            self.assertEqual(json.loads((folder / 'fast.json').read_text())['rate'], '+6%')

        with tempfile.TemporaryDirectory() as tmp, \
                patch.object(voice.edge_tts, 'Communicate', return_value=Request()) as provider, \
                patch.object(voice, 'probe_duration', return_value=1.2):
            asyncio.run(exercise(Path(tmp), provider))


class VoicePronunciationTests(unittest.TestCase):
    def test_provider_gets_chong_but_captions_keep_zhong_character(self):
        class Request:
            async def stream(self):
                yield {'type': 'audio', 'data': b'audio'}
                for i, text in enumerate(['二', '崇', '五崇', '旋转']):
                    yield {'type': 'WordBoundary', 'text': text,
                           'offset': i * 3000000, 'duration': 2000000}

        async def exercise(folder, provider):
            line = {'id': 'rotations', 'text': '二重、五重旋转。'}
            config = {'voice': 'test', 'pronunciations': {'二重': '二崇', '五重': '五崇'}}
            result = await voice.synthesize(line, config, folder)
            self.assertEqual(provider.call_args.args[0], '二崇、五崇旋转。')
            self.assertEqual(result['text'], line['text'])
            self.assertEqual([w['text'] for w in result['words']], ['二', '重', '五重', '旋转'])
            self.assertEqual(result['words'][2]['start'], .6)
            self.assertEqual(result['words'][2]['spokenText'], '五崇')
            self.assertNotEqual(voice_fingerprint(line, config), voice_fingerprint(line, {'voice': 'test'}))
            await voice.synthesize(line, config, folder)
            self.assertEqual(provider.call_count, 1)
            config['pronunciations']['五重'] = '五虫'
            await voice.synthesize(line, config, folder)
            self.assertEqual(provider.call_count, 2)

        with tempfile.TemporaryDirectory() as tmp, \
                patch.object(voice.edge_tts, 'Communicate', return_value=Request()) as provider, \
                patch.object(voice, 'probe_duration', return_value=1.2):
            # The second synthesis changes provider text, so return matching words.
            original = Request.stream
            async def stream(request):
                async for item in original(request):
                    if item.get('text') == '五崇' and provider.call_args.args[0].find('五虫') >= 0:
                        item = {**item, 'text': '五虫'}
                    yield item
            with patch.object(Request, 'stream', stream):
                asyncio.run(exercise(Path(tmp), provider))

    def test_rules_do_not_change_unrelated_polyphones_or_legacy_cache(self):
        line = {'id': 'meaning', 'text': '这个顺序很重要。'}
        config = {'voice': 'test', 'pronunciations': {'五重': '五崇'}}
        self.assertEqual(effective_speech_text(line, config), line['text'])
        self.assertEqual(voice_fingerprint(line, config), voice_fingerprint(line, {'voice': 'test'}))

    def test_longest_match_line_override_and_no_cascading(self):
        config = {'pronunciations': {'五重': '五崇', '五重对称': '五虫对称', '崇': '虫'}}
        line = {'text': '五重对称，五重旋转。', 'pronunciations': {'五重对称': '五崇对称'}}
        self.assertEqual(effective_speech_text(line, config), '五崇对称，五崇旋转。')

    def test_ambiguous_offset_or_length_changes_fail_closed(self):
        for rules in ([], {'五重': 'chong'}, {'五重': '崇'}, {'': ''}):
            with self.subTest(rules=rules), self.assertRaises(ValueError):
                effective_speech_text({'text': '五重'}, {'pronunciations': rules})
        with self.assertRaisesRegex(ValueError, 'Cannot align'):
            restore_word_texts([{'text': '未知', 'start': 0, 'end': 1}], '五崇', '五重')


if __name__ == '__main__':
    unittest.main()

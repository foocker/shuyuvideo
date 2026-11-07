import asyncio
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'sound'))
import voice


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


if __name__ == '__main__':
    unittest.main()

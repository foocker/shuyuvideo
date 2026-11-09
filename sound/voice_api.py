"""Doubao SSE / MiniMax HTTP adapters using provider-native word timestamps."""
import base64
import binascii
from http.client import HTTPException
import json
import math
import uuid
import wave
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen, build_opener, HTTPRedirectHandler

from voice_config import spoken_positions
from voice_roles import credentials


class VoiceAPIError(RuntimeError):
    pass


class NoAuthRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # API endpoints are explicit; do not forward credentials on a redirect.
        return None


def open_request(request):
    # Do not print response bodies, headers, signed subtitle URLs or raw exceptions.
    try:
        if request.get_method() == 'POST':
            return build_opener(NoAuthRedirect()).open(request, timeout=120)
        return urlopen(request, timeout=120)
    except HTTPError as exc:
        raise VoiceAPIError(f'Voice API HTTP {exc.code}; check credentials, access and quota in the provider console') from None
    except (URLError, TimeoutError, OSError):
        raise VoiceAPIError('Voice API network request failed; check connection and endpoint') from None


def rate_percent(rate):
    value = int(rate.rstrip('%'))
    if not -50 <= value <= 100:
        raise ValueError('API voice rate must be between -50% and +100%')
    return value


def request_spec(text, rate, profile, env):
    headers = {'Content-Type': 'application/json', **credentials(profile, env)}
    percent = rate_percent(rate)
    if profile['provider'] == 'doubao':
        headers.update({'Accept': 'text/event-stream', 'X-Api-Resource-Id': profile['resource_id'],
                        'X-Api-Request-Id': str(uuid.uuid4())})
        params = {'text': text, 'speaker': profile['voice'], 'audio_params': {
            'format': 'pcm', 'sample_rate': profile['sample_rate'],
            'speech_rate': percent, 'enable_subtitle': True}}
        if profile.get('model'):
            params['model'] = profile['model']
        body = {'user': {'uid': 'shuyu'}, 'req_params': params}
    elif profile['provider'] == 'minimax':
        body = {'model': profile['model'], 'text': text, 'stream': False,
                'voice_setting': {'voice_id': profile['voice'], 'speed': 1 + percent / 100,
                                  'vol': 1, 'pitch': 0},
                'audio_setting': {'sample_rate': profile['sample_rate'], 'format': 'pcm', 'channel': 1},
                'subtitle_enable': True, 'subtitle_type': 'word', 'output_format': 'hex',
                'language_boost': 'Chinese'}
    else:
        raise ValueError('Unsupported API provider')
    return Request(profile['endpoint'], data=json.dumps(body, ensure_ascii=False).encode('utf-8'),
                   headers=headers, method='POST')


def sse_events(lines):
    data = []
    for raw in lines:
        line = raw.decode('utf-8').rstrip('\r\n')
        if not line:
            if data:
                yield json.loads('\n'.join(data))
                data = []
        elif line.startswith('data:'):
            data.append(line[5:].lstrip())
    if data:
        yield json.loads('\n'.join(data))


def parse_doubao(lines):
    audio, words, complete = bytearray(), [], False
    for event in sse_events(lines):
        code = event.get('code')
        if code not in (0, 20000000):
            safe_code = code if isinstance(code, int) else 'unknown'
            raise VoiceAPIError(f'Doubao synthesis failed (code {safe_code}); check provider console')
        if event.get('data'):
            audio.extend(base64.b64decode(event['data'], validate=True))
        sentence = event.get('sentence') or {}
        for word in sentence.get('words') or []:
            words.append({'text': word['word'], 'start': word['startTime'], 'end': word['endTime']})
        if code == 20000000:
            complete = True
    if not complete:
        raise VoiceAPIError('Doubao stream ended without terminal success; no take was published')
    return bytes(audio), words


def parse_minimax(payload, fetch_subtitles):
    code = (payload.get('base_resp') or {}).get('status_code')
    if code != 0:
        safe_code = code if isinstance(code, int) else 'unknown'
        raise VoiceAPIError(f'MiniMax synthesis failed (code {safe_code}); check provider console')
    data = payload.get('data') or {}
    audio = bytes.fromhex(data.get('audio') or '')
    link = data.get('subtitle_file')
    if not link:
        raise VoiceAPIError('MiniMax returned no word subtitle file; no take was published')
    # A separate unauthenticated request: never forward the synthesis API key.
    parts = urlsplit(link)
    if parts.scheme != 'https' or not parts.netloc or parts.username or parts.password:
        raise VoiceAPIError('MiniMax returned an invalid subtitle download URL')
    segments = fetch_subtitles(link)
    if not isinstance(segments, list):
        raise VoiceAPIError('MiniMax subtitle response must contain a list of segments')
    words = []
    for segment in segments:
        for word in segment.get('timestamped_words') or []:
            words.append({'text': word['word'], 'start': word['time_begin'] / 1000,
                          'end': word['time_end'] / 1000})
    return audio, words


def download_subtitles(link):
    with open_request(Request(link, headers={'Accept': 'application/json'})) as response:
        return json.load(response)


def validate_words(words, spoken, duration):
    if not words:
        raise VoiceAPIError('Provider returned no word timestamps; sentence timing cannot drive the animation')
    checked = []
    for word in words:
        start, end = float(word['start']), float(word['end'])
        if (not isinstance(word['text'], str) or not word['text']
                or not math.isfinite(start) or not math.isfinite(end)
                or start < 0 or end <= start or end > duration + .15):
            raise VoiceAPIError('Provider returned invalid word timestamps; no take was published')
        checked.append({'text': word['text'], 'start': round(start, 3), 'end': round(end, 3)})
    checked.sort(key=lambda w: (w['start'], w['end']))
    canonical = lambda text: ''.join(text[i] for i in spoken_positions(text))
    if canonical(''.join(w['text'] for w in checked)) != canonical(spoken):
        raise VoiceAPIError('Provider word subtitles do not cover the spoken text exactly; no take was published')
    return checked


def synthesize_api(text, rate, profile, env, dest):
    try:
        request = request_spec(text, rate, profile, env)
        with open_request(request) as response:
            if profile['provider'] == 'doubao':
                audio, words = parse_doubao(response)
            else:
                audio, words = parse_minimax(json.load(response), download_subtitles)
        if not audio or len(audio) % 2:
            raise VoiceAPIError('Provider returned empty or incomplete PCM audio; no take was published')
        duration = len(audio) / (2 * profile['sample_rate'])
        words = validate_words(words, text, duration)
        with wave.open(str(dest), 'wb') as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(profile['sample_rate'])
            output.writeframes(audio)
        return words
    except VoiceAPIError:
        raise
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError, UnicodeError, binascii.Error):
        raise VoiceAPIError('Malformed voice API response; no take was published') from None
    except (URLError, TimeoutError, OSError, HTTPException):
        raise VoiceAPIError('Voice API transfer failed; no take was published') from None

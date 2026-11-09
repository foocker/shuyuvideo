"""Narrator roles and literal .env configuration; credentials never enter profiles."""
import os
from pathlib import Path
import re
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / '.env'
ROLES = {
    'default': ('当前讲解员（稿件中的 Edge 音色）', 'edge', None),
    'doubao-magnetic': ('豆包 · 磁性解说男声 2.0', 'doubao', 'zh_male_cixingjieshuonan_uranus_bigtts'),
    'doubao-young': ('豆包 · 阳光青年 2.0', 'doubao', 'zh_male_yangguangqingnian_uranus_bigtts'),
    'minimax-gentle': ('MiniMax · 温润青年', 'minimax', 'Chinese (Mandarin)_Gentle_Youth'),
    'minimax-elite': ('MiniMax · 精英青年', 'minimax', 'male-qn-jingying'),
    'doubao-custom': ('豆包 · 自定义／克隆音色', 'doubao', None),
    'minimax-custom': ('MiniMax · 自定义／克隆音色', 'minimax', None),
}


def read_env(path=ENV_FILE, environ=None):
    """Read UTF-8 literals (no shell execution or variable expansion). OS wins."""
    values = {}
    if path.exists():
        for number, raw in enumerate(path.read_text(encoding='utf-8-sig').splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('export '):
                line = line[7:].lstrip()
            key, sep, value = line.partition('=')
            key, value = key.strip(), value.strip()
            if not sep or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', key):
                raise ValueError(f'.env line {number}: expected NAME=value')
            if value.startswith(('"', "'")):
                if len(value) < 2 or value[-1] != value[0]:
                    raise ValueError(f'.env line {number}: unmatched quote')
                value = value[1:-1]
            else:
                value = re.split(r'\s+#', value, maxsplit=1)[0].rstrip()
            values[key] = value
    values.update(os.environ if environ is None else environ)
    return values


def resolve_role(config, role=None, env=None):
    env = read_env() if env is None else env
    role = role or env.get('SHUYU_VOICE_ROLE') or 'default'
    if role not in ROLES:
        raise ValueError('Unknown voice role; use --list-roles')
    _, provider, voice_id = ROLES[role]
    profile = {'role': role, 'provider': provider, 'voice': config.get('voice', '')}
    if provider == 'edge':
        if not profile['voice']:
            raise ValueError('narration.json must name the default Edge voice')
        return profile
    prefix = provider.upper()
    voice_id = voice_id or env.get(f'{prefix}_VOICE_ID', '')
    if not voice_id:
        raise ValueError(f'{role}: fill {prefix}_VOICE_ID in tools/shuyuvideo/.env')
    profile['voice'] = voice_id
    if provider == 'doubao':
        resource = env.get('DOUBAO_RESOURCE_ID') or 'seed-tts-2.0'
        # This adapter requires the word subtitles provided by TTS/ICL 2.0.
        if resource not in ('seed-tts-2.0', 'seed-tts-2.0-concurr', 'seed-icl-2.0', 'seed-icl-2.0-concurr'):
            raise ValueError('DOUBAO_RESOURCE_ID must select a TTS 2.0 or ICL 2.0 resource')
        profile.update(resource_id=resource, sample_rate=24000,
                       endpoint=env.get('DOUBAO_TTS_URL') or
                       'https://openspeech.bytedance.com/api/v3/tts/unidirectional/sse')
        if env.get('DOUBAO_MODEL'):
            if not resource.startswith('seed-icl-2.0'):
                raise ValueError('DOUBAO_MODEL is only used with an ICL 2.0 clone resource')
            profile['model'] = env['DOUBAO_MODEL']
    else:
        profile.update(model=env.get('MINIMAX_MODEL') or 'speech-2.8-hd', sample_rate=44100,
                       endpoint=env.get('MINIMAX_TTS_URL') or 'https://api.minimax.cn/v1/t2a_v2')
    endpoint = urlsplit(profile['endpoint'])
    if (endpoint.scheme != 'https' or not endpoint.netloc or endpoint.username
            or endpoint.password or endpoint.query or endpoint.fragment):
        raise ValueError(f'{prefix}_TTS_URL must be HTTPS without credentials, query or fragment')
    return profile


def credentials(profile, env):
    provider = profile['provider']
    if provider == 'edge':
        return {}
    if provider == 'minimax' and env.get('MINIMAX_API_KEY'):
        return {'Authorization': 'Bearer ' + env['MINIMAX_API_KEY']}
    if provider == 'doubao':
        if env.get('DOUBAO_API_KEY'):
            return {'X-Api-Key': env['DOUBAO_API_KEY']}
        if env.get('DOUBAO_APP_ID') and env.get('DOUBAO_ACCESS_TOKEN'):
            return {'X-Api-App-Id': env['DOUBAO_APP_ID'], 'X-Api-Access-Key': env['DOUBAO_ACCESS_TOKEN']}
    raise ValueError(f'{provider}: fill API credentials in tools/shuyuvideo/.env (never in the manuscript)')


def credential_ready(profile, env):
    try:
        credentials(profile, env)
        return True
    except ValueError:
        return False

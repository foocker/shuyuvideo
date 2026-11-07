"""Resolve narration settings identically for synthesis and cache validation."""
import hashlib
import json
import re


def effective_rate(line, config):
    rate = line.get('rate', config.get('rate', '+0%'))
    if not isinstance(rate, str) or not re.fullmatch(r'[+-]\d+%', rate):
        raise ValueError(f"{line.get('id', 'voice')}.rate: expected a signed percentage, e.g. +8%")
    return rate


def voice_fingerprint(line, config):
    # Keep the historical key for lines that inherit the global rate.
    key = [line['text'], config['voice'], effective_rate(line, config)]
    return hashlib.sha256(json.dumps(key, ensure_ascii=False).encode('utf-8')).hexdigest()

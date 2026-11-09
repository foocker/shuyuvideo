"""Resolve narration settings identically for synthesis and cache validation."""
import hashlib
import json
import re


def effective_rate(line, config):
    rate = line.get('rate', config.get('rate', '+0%'))
    if not isinstance(rate, str) or not re.fullmatch(r'[+-]\d+%', rate):
        raise ValueError(f"{line.get('id', 'voice')}.rate: expected a signed percentage, e.g. +8%")
    return rate


def effective_speech_text(line, config):
    """Apply explicit, equal-length Mandarin pronunciation hints to TTS only.

    Equal-length substitutions let provider word offsets map back to the exact
    manuscript. Apply longest matches once, so hints cannot cascade.
    """
    rules = {}
    for settings in (config, line):
        values = settings.get('pronunciations', {})
        if not isinstance(values, dict):
            raise ValueError('pronunciations: expected an object of Chinese term replacements')
        for source, target in values.items():
            if (not isinstance(source, str) or not isinstance(target, str)
                    or not re.fullmatch(r'[\u3400-\u9fff]+', source)
                    or not re.fullmatch(r'[\u3400-\u9fff]+', target)
                    or len(source) != len(target)):
                raise ValueError('pronunciations: source and target must be equal-length Chinese text')
            rules[source] = target
    if not rules:
        return line['text']
    pattern = '|'.join(re.escape(key) for key in sorted(rules, key=lambda key: (-len(key), key)))
    return re.sub(pattern, lambda match: rules[match.group()], line['text'])


def restore_word_texts(words, spoken, original):
    """Keep actual timestamps but expose manuscript characters to captions/anchors."""
    if spoken == original:
        return words
    if len(spoken) != len(original):
        raise ValueError('Pronunciation text length differs from the manuscript')
    cursor = 0
    restored = []
    for word in words:
        start = spoken.find(word['text'], cursor)
        if start < 0:
            raise ValueError(f"Cannot align pronunciation word {word['text']!r} to source text")
        cursor = start + len(word['text'])
        row = {**word, 'text': original[start:cursor]}
        if row['text'] != word['text']:
            row['spokenText'] = word['text']
        restored.append(row)
    return restored


def voice_fingerprint(line, config):
    # Keep the historical key for lines that inherit the global rate.
    key = [line['text'], config['voice'], effective_rate(line, config)]
    spoken = effective_speech_text(line, config)
    if spoken != line['text']:
        key.append({'spokenText': spoken})
    return hashlib.sha256(json.dumps(key, ensure_ascii=False).encode('utf-8')).hexdigest()

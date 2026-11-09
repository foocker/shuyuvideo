"""Resolve narration settings identically for synthesis and cache validation."""
import hashlib
import json
import re
import unicodedata


def spoken_positions(text):
    """Positions of spoken characters, excluding punctuation and whitespace."""
    return [i for i, ch in enumerate(text)
            if not ch.isspace() and not unicodedata.category(ch).startswith('P')]


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
    source = line['text']
    spoken = line.get('speechText', source)
    if not isinstance(spoken, str) or not spoken.strip():
        raise ValueError('speechText: expected non-empty text')
    if ''.join(spoken[i] for i in spoken_positions(spoken)) != ''.join(
            source[i] for i in spoken_positions(source)):
        raise ValueError('speechText may only change punctuation or whitespace; edit the manuscript to change words')
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
        return spoken
    pattern = '|'.join(re.escape(key) for key in sorted(rules, key=lambda key: (-len(key), key)))
    return re.sub(pattern, lambda match: rules[match.group()], spoken)


def restore_word_texts(words, spoken, original):
    """Keep actual timestamps but expose manuscript characters to captions/anchors."""
    if spoken == original:
        return words
    spoken_chars = spoken_positions(spoken)
    original_chars = spoken_positions(original)
    if len(spoken_chars) != len(original_chars):
        raise ValueError('Pronunciation text length differs from the manuscript')
    spoken_letters = ''.join(spoken[i] for i in spoken_chars)
    cursor = 0
    restored = []
    for word in words:
        letters = ''.join(word['text'][i] for i in spoken_positions(word['text']))
        if not letters:
            continue
        if not spoken_letters.startswith(letters, cursor):
            raise ValueError(f"Cannot align pronunciation word {word['text']!r} to source text")
        positions = original_chars[cursor:cursor + len(letters)]
        cursor += len(letters)
        row = {**word, 'text': original[positions[0]:positions[-1] + 1]}
        if row['text'] != word['text']:
            row['spokenText'] = word['text']
        restored.append(row)
    return restored


def voice_fingerprint(line, config, profile=None):
    # Keep the historical key for lines that inherit the global rate.
    key = [line['text'], config['voice'], effective_rate(line, config)]
    spoken = effective_speech_text(line, config)
    if spoken != line['text']:
        key.append({'spokenText': spoken})
    if profile and profile['provider'] != 'edge':
        # API sound identity is independent of the unused manuscript Edge voice.
        key[1] = profile['voice']
        key.append({'voiceProfile': profile})
    return hashlib.sha256(json.dumps(key, ensure_ascii=False).encode('utf-8')).hexdigest()

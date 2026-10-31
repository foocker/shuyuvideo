"""Explicit Manim helpers using the repository's shared color tokens.

No import-time Manim defaults are changed. Call apply(scene), then use helpers
or COLORS by semantic role. Tested with local Manim CE 0.21.0 only.
"""
import json
from pathlib import Path

from manim import Text, MathTex

TOKENS = json.loads((Path(__file__).resolve().parents[1] / 'tokens.json').read_text(encoding='utf-8'))
COLORS = TOKENS['colors']


def apply(scene):
    scene.camera.background_color = COLORS['background']


def text(content, *, role='ink', font_size=32, **kwargs):
    kwargs.setdefault('font', TOKENS['typography']['sans'])
    kwargs.setdefault('color', COLORS[role])
    return Text(content, font_size=font_size, **kwargs)


def mathtex(*expressions, role='ink', font_size=44, **kwargs):
    kwargs.setdefault('color', COLORS[role])
    return MathTex(*expressions, font_size=font_size, **kwargs)

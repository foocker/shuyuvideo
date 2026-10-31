"""A static style proof, not an imported Math-To-Manim scene or a finished film.

python -m manim -s --disable_caching -r 1920,1080 --media_dir style/evidence/manim style/adapters/manim_style_proof.py ShuyuStyleProof
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from manim import Scene, Circle, Dot, Line, DashedLine, Axes, UP, DOWN, LEFT
import manim_theme as shuyu


class ShuyuStyleProof(Scene):
    def construct(self):
        shuyu.apply(self)
        c = shuyu.COLORS
        title = shuyu.text('圆周与它的投影', font_size=42, weight='MEDIUM').to_edge(UP, buff=.48)
        subtitle = shuyu.text('同一个角度，连接同一高度。', role='muted', font_size=23).next_to(title, DOWN, buff=.2)
        radius = 1.5
        axes = Axes(x_range=[0, 2*np.pi, np.pi/2], y_range=[-1, 1, 1],
                    x_length=4.8, y_length=3, tips=False,
                    axis_config={'color': c['ink'], 'stroke_width': 2, 'include_ticks': False}).move_to([2.65, -.1, 0])
        center = np.array([-3.7, axes.c2p(0, 0)[1], 0])
        circle = Circle(radius=radius, color=c['subject'], stroke_width=5).move_to(center)
        horizontal = Line(center+[-1.8, 0, 0], center+[1.8, 0, 0], color=c['line'], stroke_width=1.8)
        vertical = Line(center+[0, -1.75, 0], center+[0, 1.75, 0], color=c['line'], stroke_width=1.8)
        curve = axes.plot(np.sin, x_range=[0, 2*np.pi, .025], color=c['subject'], stroke_width=5)
        angle = .95
        point = center+radius*np.array([np.cos(angle), np.sin(angle), 0])
        target = axes.c2p(angle, np.sin(angle))
        assert abs(point[1]-target[1]) < 1e-8
        radial = Line(center, point, color=c['emphasis'], stroke_width=3)
        projection = DashedLine(point, target, color=c['emphasis'], stroke_width=2.4, dash_length=.09)
        a = Dot(point, radius=.075, color=c['focus']).set_stroke(c['backface'], width=1.5)
        b = Dot(target, radius=.075, color=c['focus']).set_stroke(c['backface'], width=1.5)
        theta = shuyu.mathtex(r'\theta', role='emphasis', font_size=35).move_to(center+[.55, .23, 0])
        x_label = shuyu.mathtex(r'\theta', font_size=30).next_to(axes.x_axis, direction=np.array([1,0,0]), buff=.17)
        y_label = shuyu.mathtex('y', font_size=30).next_to(axes.y_axis, UP, buff=.13)
        equation = shuyu.mathtex(r'x=\cos\theta', r'\qquad', r'y=\sin\theta', font_size=43).to_edge(DOWN, buff=.63)
        equation[2].set_color(c['emphasis'])
        self.add(title, subtitle, horizontal, vertical, axes, circle, curve, radial, projection, a, b, theta, x_label, y_label, equation)

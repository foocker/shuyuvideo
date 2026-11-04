import importlib.util
import io
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'motion/checks' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SvgTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.svg = load('svg_audit')
        except ImportError as exc:
            raise unittest.SkipTest(str(exc))

    def test_arc_and_smooth_commands_are_supported(self):
        result = self.svg.inspect_path('M0 0 A10 10 0 0 1 10 10 Q15 10 20 0 T40 0 C45 0 45 10 50 10 S55 0 60 0', 8)
        self.assertGreaterEqual(result['segments'], 5)

    def test_smooth_curve_and_intentional_corner(self):
        smooth = self.svg.inspect_path('M0 0 C10 0 20 0 30 0 C40 0 50 0 60 0', 8)
        self.assertEqual(smooth['warnings'], [])
        corner = self.svg.inspect_path('M0 0 L10 0 L10 10', 8)
        self.assertEqual(corner['warnings'][0]['degrees'], 90)

    def test_unknown_command_is_not_silently_skipped(self):
        with self.assertRaises(ValueError):
            self.svg.inspect_path('M0 0 R10 20', 8)


class ImageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.probe = load('probe_motion')
            from PIL import Image
            cls.Image = Image
        except ImportError as exc:
            raise unittest.SkipTest(str(exc))

    def png(self, color, size=(2, 2)):
        buffer = io.BytesIO()
        self.Image.new('RGBA', size, color).save(buffer, format='PNG')
        return buffer.getvalue()

    def test_rgb_difference_with_equal_alpha_is_detected(self):
        a, b = self.png((0, 0, 0, 255)), self.png((255, 0, 0, 255))
        self.assertFalse(self.probe.difference(a, b)['identical'])
        self.assertTrue(self.probe.difference(a, a)['identical'])

    def test_size_mismatch_is_not_rescaled(self):
        with self.assertRaises(ValueError):
            self.probe.difference(self.png('white'), self.png('white', (3, 3)))


class TilingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('check_geometry', ROOT / 'examples/staircase/check_geometry.py')
        cls.geometry = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.geometry)

    def test_disjoint_cover_passes_but_missing_block_fails(self):
        rect = {'x': 0, 'y': 0, 'width': 2, 'height': 1}
        blocks = [{'x': i, 'y': 0, 'width': 1, 'height': 1} for i in range(2)]
        self.assertEqual(self.geometry.tiling_errors(blocks, rect), [])
        self.assertTrue(self.geometry.tiling_errors(blocks[:1], rect))

    def test_equal_area_with_overlap_or_offset_fails(self):
        rect = {'x': 0, 'y': 0, 'width': 2, 'height': 1}
        a = {'x': 0, 'y': 0, 'width': 1, 'height': 1}
        self.assertTrue(self.geometry.tiling_errors([a, a], rect))
        b = {'x': 1, 'y': -0.3, 'width': 1, 'height': 1}
        self.assertTrue(self.geometry.tiling_errors([a, b], rect))


if __name__ == '__main__':
    unittest.main()

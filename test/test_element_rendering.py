import unittest

from bowl import CursorTreeRenderer

__all__ = ["TestCursorTreeRenderer"]

class TestCursorTreeRenderer(unittest.TestCase):

    def test_static_offset(self):
        gao = CursorTreeRenderer.get_absolute_offset
        gro = CursorTreeRenderer.get_relative_offset

        self.assertEqual(0, gao(0.0, 6))
        self.assertEqual(1, gao(0.2, 6))
        self.assertEqual(2, gao(0.4, 6))
        self.assertEqual(3, gao(0.6, 6))
        self.assertEqual(4, gao(0.8, 6))
        self.assertEqual(5, gao(1.0, 6))

        for i in range(1, 1000):
            self.assertEqual(0, gao(0.0, i))
            self.assertEqual(i, gao(1.0, i + 1))

        height = 1000
        for i in range(height):
            self.assertEqual(i, gao(gro(i, height), height))

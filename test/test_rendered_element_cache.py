import unittest

from cheuph import Element, RenderedElementCache

__all__ = ["TestRenderedElementCache"]

class TestRenderedElementCache(unittest.TestCase):

    def setUp(self):
        self.cache = RenderedElementCache()
        self.e1 = Element("e1", None)
        self.e2 = Element("e2", "e1")
        self.e3 = Element("e3", "xyz")
        self.e1_2 = Element("e1", "bla")

    def test_adding_and_getting(self):
        self.assertEqual(self.cache.get("e1"), None)
        self.assertEqual(self.cache.get("e2"), None)

        self.cache.add(self.e1)
        self.assertEqual(self.cache.get("e1"), self.e1)

        self.cache.add(self.e2)
        self.assertEqual(self.cache.get("e2"), self.e2)

        self.cache.add(self.e1_2)
        self.assertEqual(self.cache.get("e1"), self.e1_2)

        self.assertEqual(self.cache.get("e3"), None)
        self.cache.add(self.e3)
        self.assertEqual(self.cache.get("e3"), self.e3)

    def test_invalidating(self):
        self.assertEqual(self.cache.get("e1"), None)
        self.assertEqual(self.cache.get("e2"), None)
        self.cache.add(self.e1)
        self.cache.add(self.e2)
        self.assertEqual(self.cache.get("e1"), self.e1)
        self.assertEqual(self.cache.get("e2"), self.e2)

        self.cache.invalidate("e1")

        self.assertEqual(self.cache.get("e1"), None)
        self.assertEqual(self.cache.get("e2"), self.e2)

        self.cache.add(self.e1)
        self.cache.invalidate_all()

        self.assertEqual(self.cache.get("e1"), None)
        self.assertEqual(self.cache.get("e2"), None)

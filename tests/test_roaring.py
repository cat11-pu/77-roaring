import unittest

from bitmapapi import Index
from roaring import Bitmap


class TestBitmap(unittest.TestCase):
    def test_add_counts(self):
        self.assertEqual(Bitmap().add(5)["size"], 1)

    def test_members_sorted(self):
        bitmap = Bitmap()
        bitmap.add(9)
        bitmap.add(3)
        self.assertEqual(bitmap.members(), [3, 9])

    def test_members_empty(self):
        self.assertEqual(Bitmap().members(), [])

    def test_stats_shape(self):
        self.assertIn("containers", Bitmap().stats())

    def test_index_wraps_bitmap(self):
        index = Index()
        index.add(1)
        self.assertEqual(index.bitmap.stats()["size"], 1)


if __name__ == "__main__":
    unittest.main()

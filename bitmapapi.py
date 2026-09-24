"""bitmapapi.py：对外门面（老接口 add/members 不能改）。"""
from __future__ import annotations

from roaring import Bitmap


class Index:
    def __init__(self):
        self.bitmap = Bitmap()

    def add(self, value: int) -> dict:
        return self.bitmap.add(value)

    def members(self) -> list:
        return self.bitmap.members()

    def pick_containers(self) -> dict:
        return self.bitmap.pick_containers()

    def union(self, other) -> "Index":
        return self.bitmap.union(other.bitmap if hasattr(other, "bitmap") else other)

    def intersect(self, other) -> "Index":
        return self.bitmap.intersect(other.bitmap if hasattr(other, "bitmap") else other)

    def snapshot(self) -> bytes:
        return self.bitmap.persist()

    def rebuild(self, blob: bytes = None) -> dict:
        return self.bitmap.restore(blob)

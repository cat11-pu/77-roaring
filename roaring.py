"""roaring.py：按高 16 位分容器的压缩位图（纯标准库）。"""
from __future__ import annotations

import struct

ARRAY_LIMIT = 8
HEADER_BYTES = 4
BITMAP_BYTES = 8192


def _kind(count: int) -> str:
    return "array" if count <= ARRAY_LIMIT else "bitmap"


class Bitmap:
    def __init__(self):
        self.containers = {}
        self._size = 0

    def add(self, value: int) -> dict:
        key, low = divmod(value, 1 << 16)
        bucket = self.containers.setdefault(key, set())
        if low not in bucket:
            self._size += 1
        bucket.add(low)
        return {"size": self._size}

    def members(self) -> list:
        out = []
        for key in sorted(self.containers):
            for low in sorted(self.containers[key]):
                out.append((key << 16) | low)
        return out

    def pick_containers(self) -> dict:
        kinds = {}
        for key in sorted(self.containers):
            kinds[str(key)] = _kind(len(self.containers[key]))
        return {"kinds": kinds}

    def serialized_size(self) -> int:
        total = 0
        for lows in self.containers.values():
            total += HEADER_BYTES
            total += 2 * len(lows) if len(lows) <= ARRAY_LIMIT else BITMAP_BYTES
        return total

    def union(self, other) -> "Bitmap":
        result = Bitmap()
        for key in set(self.containers) | set(other.containers):
            merged = set(self.containers.get(key, ()))
            merged |= other.containers.get(key, set())
            result.containers[key] = merged
            result._size += len(merged)
        return result

    def intersect(self, other) -> "Bitmap":
        result = Bitmap()
        for key in set(self.containers) & set(other.containers):
            common = self.containers[key] & other.containers[key]
            if common:
                result.containers[key] = common
                result._size += len(common)
        return result

    def persist(self) -> bytes:
        chunks = []
        for key in sorted(self.containers):
            lows = sorted(self.containers[key])
            chunks.append(struct.pack("<HH", key, len(lows)))
            chunks.append(struct.pack("<%dH" % len(lows), *lows))
        return b"".join(chunks)

    def restore(self, blob: bytes = None) -> dict:
        self.containers = {}
        self._size = 0
        data = blob or b""
        offset = 0
        while offset < len(data):
            key, count = struct.unpack_from("<HH", data, offset)
            offset += 4
            lows = struct.unpack_from("<%dH" % count, data, offset)
            offset += 2 * count
            self.containers[key] = set(lows)
            self._size += len(self.containers[key])
        return {"size": self._size}

    def stats(self) -> dict:
        return {"size": self._size, "containers": len(self.containers)}

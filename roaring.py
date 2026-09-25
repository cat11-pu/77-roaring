"""roaring.py：容器化压缩位图（高 16 位分容器，数组/位图双形态）。"""
from __future__ import annotations

import os

ARRAY_LIMIT = 8
HEADER_BYTES = 4
BITMAP_BYTES = 8192
LOW_MASK = 0xFFFF
SNAPSHOT_PATH = "roaring.snapshot"


def _bitmap_iter(bits: int):
    while bits:
        low = bits & -bits
        yield low.bit_length() - 1
        bits ^= low


class Bitmap:
    def __init__(self):
        # key（高 16 位，int）-> 容器：set 为数组容器，int 为位图容器（位掩码）
        self.containers = {}
        self._size = 0

    @staticmethod
    def _kind(container) -> str:
        return "array" if isinstance(container, set) else "bitmap"

    @staticmethod
    def _cardinality(container) -> int:
        return len(container) if isinstance(container, set) else container.bit_count()

    @staticmethod
    def _normalize(container):
        """按基数重新判定容器类型；空容器返回 None。"""
        if isinstance(container, set):
            if not container:
                return None
            if len(container) > ARRAY_LIMIT:
                bits = 0
                for low in container:
                    bits |= 1 << low
                return bits
            return container
        if container == 0:
            return None
        if container.bit_count() <= ARRAY_LIMIT:
            return set(_bitmap_iter(container))
        return container

    def add(self, value: int) -> dict:
        key = value >> 16
        low = value & LOW_MASK
        container = self.containers.get(key)
        if container is None:
            self.containers[key] = {low}
            self._size += 1
        elif isinstance(container, set):
            if low not in container:
                container.add(low)
                self._size += 1
                if len(container) > ARRAY_LIMIT:
                    self.containers[key] = self._normalize(container)
        else:
            bit = 1 << low
            if not container & bit:
                self.containers[key] = container | bit
                self._size += 1
        return {"size": self._size}

    def members(self) -> list:
        result = []
        for key in sorted(self.containers):
            container = self.containers[key]
            base = key << 16
            if isinstance(container, set):
                result.extend(base | low for low in sorted(container))
            else:
                result.extend(base | low for low in _bitmap_iter(container))
        return result

    def pick_containers(self) -> dict:
        return {
            "kinds": {
                str(key): self._kind(self.containers[key])
                for key in sorted(self.containers)
            }
        }

    def serialized_size(self) -> int:
        total = 0
        for container in self.containers.values():
            total += HEADER_BYTES
            total += 2 * len(container) if isinstance(container, set) else BITMAP_BYTES
        return total

    @staticmethod
    def _merge_union(left, right):
        if left is None:
            return right
        if right is None:
            return left
        if isinstance(left, set) and isinstance(right, set):
            return left | right
        left_bits = left if isinstance(left, int) else sum(1 << low for low in left)
        right_bits = right if isinstance(right, int) else sum(1 << low for low in right)
        return left_bits | right_bits

    @staticmethod
    def _merge_intersect(left, right):
        if isinstance(left, set) and isinstance(right, set):
            return left & right
        if isinstance(left, int) and isinstance(right, int):
            return left & right
        bits, array = (left, right) if isinstance(left, int) else (right, left)
        return {low for low in array if bits >> low & 1}

    def _combine(self, other, merger) -> "Bitmap":
        result = Bitmap()
        if merger is self._merge_intersect:
            keys = self.containers.keys() & other.containers.keys()
        else:
            keys = self.containers.keys() | other.containers.keys()
        for key in keys:
            merged = merger(self.containers.get(key), other.containers.get(key))
            merged = self._normalize(merged)
            if merged is not None:
                result.containers[key] = merged
                result._size += self._cardinality(merged)
        return result

    def union(self, other) -> "Bitmap":
        return self._combine(other, self._merge_union)

    def intersect(self, other) -> "Bitmap":
        return self._combine(other, self._merge_intersect)

    def persist(self, path: str = SNAPSHOT_PATH) -> bytes:
        blob = bytearray()
        for key in sorted(self.containers):
            container = self.containers[key]
            card = self._cardinality(container)
            blob += key.to_bytes(2, "little") + card.to_bytes(2, "little")
            if isinstance(container, set):
                for low in sorted(container):
                    blob += low.to_bytes(2, "little")
            else:
                blob += container.to_bytes(BITMAP_BYTES, "little")
        data = bytes(blob)
        with open(path, "wb") as handle:
            handle.write(data)
        return data

    def restore(self, blob: bytes = None) -> dict:
        if blob is None:
            with open(SNAPSHOT_PATH, "rb") as handle:
                blob = handle.read()
        self.containers = {}
        self._size = 0
        offset = 0
        while offset < len(blob):
            key = int.from_bytes(blob[offset:offset + 2], "little")
            card = int.from_bytes(blob[offset + 2:offset + 4], "little")
            offset += HEADER_BYTES
            if card <= ARRAY_LIMIT:
                container = {
                    int.from_bytes(blob[offset + 2 * i:offset + 2 * i + 2], "little")
                    for i in range(card)
                }
                offset += 2 * card
            else:
                container = int.from_bytes(blob[offset:offset + BITMAP_BYTES], "little")
                offset += BITMAP_BYTES
            self.containers[key] = container
            self._size += card
        return {"size": self._size, "containers": len(self.containers)}

    def stats(self) -> dict:
        return {"size": self._size, "containers": len(self.containers)}

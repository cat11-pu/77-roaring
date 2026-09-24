"""roaring.py：区间压缩位图（基线：普通集合）。"""
from __future__ import annotations


class Bitmap:
    def __init__(self):
        self.values = set()
        self.containers = {}

    def add(self, value: int) -> dict:
        """基线：集合。"""
        self.values.add(value)
        return {"size": len(self.values)}

    def members(self) -> list:
        return sorted(self.values)

    def pick_containers(self) -> dict:
        raise NotImplementedError("容器选择还没实现")

    def serialized_size(self) -> int:
        raise NotImplementedError("序列化大小还没实现")

    def union(self, other) -> "Bitmap":
        raise NotImplementedError("并集还没实现")

    def intersect(self, other) -> "Bitmap":
        raise NotImplementedError("交集还没实现")

    def persist(self) -> bytes:
        raise NotImplementedError("快照还没实现")

    def restore(self, blob: bytes = None) -> dict:
        raise NotImplementedError("重启恢复还没实现")

    def stats(self) -> dict:
        return {"size": len(self.values), "containers": len(self.containers)}

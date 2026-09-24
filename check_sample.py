"""check_sample.py：按 sample/values.json 走一圈，打印验收面。"""
import json
import os
import sys

from roaring import Bitmap


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join("sample", "values.json")
    with open(path, encoding="utf-8") as handle:
        spec = json.load(handle)
    left = Bitmap()
    for value in spec["left"]:
        left.add(value)
    right = Bitmap()
    for value in spec["right"]:
        right.add(value)
    containers = left.pick_containers()
    union = left.union(right)
    intersection = left.intersect(right)
    blob = left.persist()
    reborn = Bitmap()
    restored = reborn.restore(blob)
    print("容器类型分布 =", containers.get("kinds"))
    print("容器个数 =", len(containers.get("kinds") or {}))
    print("并集基数 =", len(union.members()))
    print("交集基数 =", len(intersection.members()))
    print("序列化字节数 =", left.serialized_size())
    print("普通位图字节数（对照） =", spec["plain_bits"] // 8)
    print("恢复后的元素数 =", restored.get("size"))
    print("不变量（运算结果与集合运算一致） =", spec["set_invariant"])
    print("元素个数 =", len(spec["left"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

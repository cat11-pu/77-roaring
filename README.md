# roaring

纯 Python 标准库的压缩位图（roaring 风格）：按值的高 16 位分容器，
容器内元素数不超过 8 用数组容器，否则用 8192 字节的位图容器。
内存与序列化大小只与实际占用的容器成正比，不按值域铺位。

## 用法

    from roaring import Bitmap

    left = Bitmap()
    left.add(100000)
    left.members()               # 升序全部值
    left.pick_containers()       # {"kinds": {"1": "array"}}
    left.serialized_size()       # 头 4 字节 + 数组 2 字节/元素，位图容器 8192 字节

    merged = left.union(other)       # 按容器对做并集，容器类型重新判定
    common = left.intersect(other)   # 按容器对做交集

    blob = left.persist()        # 落盘（roaring.snapshot）并返回字节
    reborn = Bitmap()
    reborn.restore(blob)         # 恢复后元素与容器类型一致

`bitmapapi.Index` 是对外门面，`add` / `members` / `pick_containers` /
`union` / `intersect` / `snapshot` / `rebuild` 与之一一对应。

## 测试

    python3 -m unittest discover -s tests -v

## 场景自检

    python3 check_sample.py

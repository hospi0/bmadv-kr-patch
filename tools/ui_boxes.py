# -*- coding: utf-8 -*-
"""텍스처의 글자 덩어리를 «행 밴드 → 낱말» 로 잘라 번호 오버레이와 TSV 뼈대를 낸다.

`ui_segment.py` 는 세로로 붙은 행을 하나로 뭉쳐 버린다(042 의 장 목록).
여기서는 행 피치를 그대로 살리려고 밴드를 먼저 자른다.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw


def boxes(path, gap=3, xlim=None):
    a = np.asarray(Image.open(path).convert("RGBA"))
    ink = a[..., 3] > 32
    H, W = ink.shape
    x1 = xlim or W
    out = []
    rc = ink[:, :x1].sum(axis=1)
    y = 0
    while y < H:
        if rc[y] == 0:
            y += 1
            continue
        y0 = y
        while y < H and rc[y] > 0:
            y += 1
        band = ink[y0:y, :x1]
        cc = band.sum(axis=0)
        x = 0
        while x < x1:
            if cc[x] == 0:
                x += 1
                continue
            s = x
            blank = 0
            while x < x1:
                if cc[x] == 0:
                    blank += 1
                    if blank >= gap:
                        break
                else:
                    blank = 0
                x += 1
            e = x - blank
            sub = band[:, s:e]
            ys = np.flatnonzero(sub.any(axis=1))
            out.append((s, y0 + int(ys[0]), e - s, int(ys[-1] - ys[0]) + 1))
            x += 1
    return a, out


def main():
    path = sys.argv[1]
    gap = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    a, bs = boxes(path, gap)
    name = os.path.basename(path).split(".")[0]
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "work", "ui")
    os.makedirs(root, exist_ok=True)
    im = Image.fromarray(a).convert("RGBA")
    bg = Image.new("RGBA", im.size, (0, 0, 0, 255))
    bg.alpha_composite(im)
    sc = 4
    ov = bg.convert("RGB").resize((im.size[0] * sc, im.size[1] * sc), Image.NEAREST)
    d = ImageDraw.Draw(ov)
    print("%s : 덩어리 %d개" % (name, len(bs)))
    for i, (x, y, w, h) in enumerate(bs):
        d.rectangle([x * sc, y * sc, (x + w) * sc - 1, (y + h) * sc - 1], outline=(0, 255, 0))
        d.text((x * sc + 1, y * sc + 1), str(i), fill=(255, 255, 0))
        print("  [%2d] x=%3d y=%3d w=%3d h=%2d" % (i, x, y, w, h))
    ov.save(os.path.join(root, "%s_boxes.png" % name))
    with open(os.path.join(root, "%s_boxes.tsv" % name), "w", encoding="utf-8", newline="") as f:
        f.write("x\ty\tw\th\tfont\talign\tja\tko\n")
        for x, y, w, h in bs:
            f.write("%d\t%d\t%d\t%d\tn\tl\t\t\n" % (x, y, w, h))
    print("→ work/ui/%s_boxes.png / .tsv" % name)


if __name__ == "__main__":
    main()

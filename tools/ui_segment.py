# -*- coding: utf-8 -*-
"""UI 텍스처의 «글자 덩어리»를 자동으로 잘라 좌표·색을 뽑는다.

알파(또는 잉크)로 행을 나누고, 행 안에서 빈 열이 gap 이상이면 낱말로 끊는다.
결과를 TSV 로 내보내 번역문을 적어 넣게 한다.
"""
import os
import sys

import numpy as np
from PIL import Image


def ink_mask(im):
    a = np.asarray(im.convert("RGBA"))
    if a[..., 3].max() > 0:
        return a[..., 3] > 32, a
    lum = a[..., :3].max(axis=2)
    return lum > 40, a


def segment(path, gap=3, min_w=3):
    im = Image.open(path)
    ink, a = ink_mask(im)
    h, w = ink.shape
    boxes = []
    rowcnt = ink.sum(axis=1)
    y = 0
    while y < h:
        if rowcnt[y] == 0:
            y += 1
            continue
        y0 = y
        while y < h and rowcnt[y] > 0:
            y += 1
        y1 = y - 1
        band = ink[y0:y1 + 1]
        colcnt = band.sum(axis=0)
        x = 0
        while x < w:
            if colcnt[x] == 0:
                x += 1
                continue
            x0 = x
            blank = 0
            while x < w:
                if colcnt[x] == 0:
                    blank += 1
                    if blank >= gap:
                        break
                else:
                    blank = 0
                x += 1
            x1 = x - blank
            if x1 - x0 + 1 >= min_w:
                sub = band[:, x0:x1 + 1]
                ys = np.flatnonzero(sub.any(axis=1))
                boxes.append((x0, y0 + int(ys.min()), x1 - x0 + 1, int(ys.max() - ys.min()) + 1))
            x += 1
    return im, a, ink, boxes


def main():
    path = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None
    im, a, ink, boxes = segment(path)
    name = os.path.basename(path).split(".")[0]
    print("%s : 덩어리 %d개" % (name, len(boxes)))
    rows = []
    for i, (x, y, w, h) in enumerate(boxes):
        sub = a[y:y + h, x:x + w]
        m = ink[y:y + h, x:x + w]
        px = sub[..., :3][m]
        col = tuple(int(v) for v in px.mean(axis=0)) if len(px) else (0, 0, 0)
        top = tuple(int(v) for v in sub[..., :3][m][:max(1, len(px) // 4)].mean(axis=0)) if len(px) else col
        rows.append((i, x, y, w, h, col, top))
        print("  [%3d] x=%3d y=%3d w=%3d h=%2d  평균색 %s" % (i, x, y, w, h, col))
    if out:
        with open(out, "w", encoding="utf-8", newline="") as f:
            f.write("id\tx\ty\tw\th\tr\tg\tb\tja\tko\n")
            for i, x, y, w, h, col, top in rows:
                f.write("%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t\t\n" % (i, x, y, w, h, col[0], col[1], col[2]))
        print("→ %s" % out)


if __name__ == "__main__":
    main()

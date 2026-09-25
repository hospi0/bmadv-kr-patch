# -*- coding: utf-8 -*-
"""UI 텍스처에 한글을 그려 넣는다.

번역표(TSV) 열 — x, y, w, h, font, align, xscale, kern, dx, mode, ja, ko
  font   n=갈무리11(한글 12px 폭) / c=갈무리11 Condensed(높이 같고 폭 8px, 좁은 칸 전용)
  align  l 왼쪽 / c 가운데 / r 오른쪽(상자 오른끝에 맞춰 왼쪽으로 뻗는다)
  xscale 가로 픽셀 복제 배수. 이 게임 글자는 대부분 «가로 2배» 다.
  kern   "i:±n" 목록. 그 글자의 자리 폭만 늘리거나 줄인다.
         우측 정렬에서 숫자 글리프 폭 차이가 줄머리를 4px씩 밀어 버리는 걸 잡는다.
  dx     그린 결과 전체를 가로로 민다.
  mode   t = 상자를 통째로 투명하게 지운다(기본).
         k = «배경 그림 위의 글자». 글자 픽셀만 지우고 주변 배경색으로 메운다.
              통째로 지우면 배경에 구멍이 뚫린다(044 의 ヘルプ表示 줄).

⚠️ 배경(투명) RGB 는 텍스처마다 다르다 — 001·042 는 검정, 043·044 는 초록 컬러키.
   지울 때 이 값을 그대로 채워야 게임이 투명으로 취급한다.
"""
import os
import sys

import numpy as np
from PIL import Image

from bdf import BDF

FONTDIR = r"C:\claude\utils\font\Galmuri-v2.40.3"
FONTS = {"n": "Galmuri11.bdf", "c": "Galmuri11-Condensed.bdf",
         "s": "Galmuri7.bdf", "m": "Galmuri9.bdf"}


def ink_of(a, mode):
    """글자 픽셀 판정. mode k 는 배경 그림과 섞여 있으므로 «흰 글자» 만 고른다."""
    if mode == "k":
        return (a[..., 3] > 32) & (a[..., :3].min(axis=2) > 150)
    return a[..., 3] > 32


def tight_box(ink, x, y, w, h, grow=4):
    """선언한 상자를 «잉크에 딱 맞춘 뒤» 잉크가 이어지는 동안만 넓힌다.

    ① 먼저 줄이지 않으면, 상자가 물고 있던 빈 칸을 성장 단계가 건너뛰어
       옆 라벨까지 삼킨다(鎧 가 アクセサリ 를 먹었다).
    ② 손으로 적은 h 는 1px씩 모자라기 쉽고, 그러면 원문 획이 «한 줄만» 남아
       한글 옆에 점으로 찍힌다(はずす 는 12px 이 아니라 13px 이었다).
    """
    H, W = ink.shape
    sub = ink[y:y + h, x:x + w]
    if sub.any():
        ys = np.flatnonzero(sub.any(axis=1))
        xs = np.flatnonzero(sub.any(axis=0))
        y, h = y + int(ys[0]), int(ys[-1] - ys[0]) + 1
        x, w = x + int(xs[0]), int(xs[-1] - xs[0]) + 1
    for _ in range(grow):
        if y > 0 and ink[y - 1, x:x + w].any():
            y -= 1
            h += 1
        if y + h < H and ink[y + h, x:x + w].any():
            h += 1
        if x > 0 and ink[y:y + h, x - 1].any():
            x -= 1
            w += 1
        if x + w < W and ink[y:y + h, x + w].any():
            w += 1
    return x, y, w, h


def avail_width(ink, x, y, w, h):
    """이 라벨이 «침범 없이 쓸 수 있는 폭» = 다음 라벨의 잉크가 시작되기 직전까지."""
    W = ink.shape[1]
    xx = x + w
    while xx < W and not ink[y:y + h, xx].any():
        xx += 1
    return xx - x


def row_colors(a, ink, x, y, w, h):
    """행별 «가장 밝은 잉크색».

    ⚠️ 평균을 쓰면 안 된다 — 원본 글자는 «밝은 심 + 어두운 테두리» 구조라
       평균이 갈색으로 죽는다. 행에서 가장 밝은 잉크 픽셀이 그 행의 «의도한 색» 이다.
    """
    cols = [None] * h
    for r in range(h):
        m = ink[y + r, x:x + w]
        if m.any():
            px = a[y + r, x:x + w][..., :3][m].astype(int)
            cols[r] = tuple(int(v) for v in px[px.sum(axis=1).argmax()])
    # ★★ 원문 글자에 «검은 테두리» 가 있으면, 획이 없고 테두리만 있는 줄의
    #    «가장 밝은 픽셀» 이 그 테두리 색(거의 검정)이 된다. 그 줄 색을 그대로 쓰면
    #    한글의 그 줄만 검게 나온다(HUD `메뉴` 의 ㅔ·ㅠ 아랫줄이 그랬다).
    #    상자 전체 최대 밝기의 60% 에 못 미치는 줄은 «색을 모르는 줄» 로 본다.
    lum = [None if c is None else sum(c) for c in cols]
    top = max([v for v in lum if v is not None], default=0)
    for i, v in enumerate(lum):
        if v is not None and v < top * 0.6:
            cols[i] = None
    known = [i for i, c in enumerate(cols) if c]
    if not known:
        return [(255, 255, 255)] * h
    for i in range(h):
        if cols[i] is None:
            cols[i] = cols[min(known, key=lambda k: abs(k - i))]
    return cols


def erase(a, a0, ink, x, y, w, h, bgrgb, mode):
    """원문 글자를 지운다."""
    if mode != "k":
        a[y:y + h, x:x + w, :3] = bgrgb
        a[y:y + h, x:x + w, 3] = 0
        return
    # ★ 지우기 마스크는 «흰 글자» 판정보다 넓어야 한다. 획의 흐린 가장자리는
    #   회색이라 min(rgb)>150 에 안 걸리고, 그대로 두면 그게 잔상으로 남는다.
    #   배경 그림은 아주 어두우므로(최대 채널 ~32) 60 을 넘으면 글자 쪽이다.
    ink = (a0[..., 3] > 32) & (a0[..., :3].max(axis=2) > 60)
    # 배경 그림 위 — 글자 픽셀만 지우고 «깨끗한 바탕» 으로 메운다.
    # ⚠️ 글자 바로 옆 픽셀은 획의 흐린 가장자리라 배경이 아니다. 마스크를 2px 부풀린다.
    # ⚠️ 열 전체의 중앙값을 쓰면 안 된다 — 이 그림은 아래로 갈수록 밝아서 중앙값이
    #    위로 뜨고, 밝아진 바탕 사이로 원문 획이 다시 비친다.
    #    바깥에서 안으로 «한 겹씩» 이웃 평균으로 메워 국소 밝기를 따라가게 한다.
    H, W = ink.shape
    big = ink.copy()
    for _ in range(2):
        g = big.copy()
        g[1:, :] |= big[:-1, :]
        g[:-1, :] |= big[1:, :]
        g[:, 1:] |= big[:, :-1]
        g[:, :-1] |= big[:, 1:]
        big = g
    # 지우는 창은 상자보다 넓다 — 흐린 가장자리가 상자 밖 행까지 뻗어 있다.
    ey0, ey1 = max(0, y - 3), min(H, y + h + 3)
    ex0, ex1 = max(0, x - 3), min(W, x + w + 3)
    win = np.zeros((H, W), bool)
    win[ey0:ey1, ex0:ex1] = True
    unknown = big & win
    val = a[..., :3].astype(np.float32)
    # 소스에서 «글자 픽셀 전부» 를 뺀다. 창 경계 밖에 남은 옆 라벨의 흰 획을
    # 배경으로 삼으면 그 흰색이 안으로 빨려 들어온다(x=134~137 이 205,205,205 가 됐다).
    known = (a[..., 3] > 32) & ~big
    for _ in range(40):
        if not unknown.any():
            break
        s = np.zeros_like(val)
        c = np.zeros((H, W), np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            v = np.roll(np.where(known[..., None], val, 0), (dy, dx), (0, 1))
            k = np.roll(known.astype(np.float32), (dy, dx), (0, 1))
            s += v
            c += k
        fill = unknown & (c > 0)
        if not fill.any():
            break
        val[fill] = s[fill] / c[fill, None]
        known |= fill
        unknown &= ~fill
    m = big & win
    a[..., :3][m] = np.rint(val[m]).astype(np.uint8)
    a[..., 3][m] = 255


def row_coverage(bits, xscale, aa):
    """글리프 한 «행» 의 0/1 비트 → 가로 방향 커버리지(0~1).

    ⛔ 사방으로 0.5 픽셀을 두르면 안티가 아니라 **테두리** 가 된다.
    ⛔ 복제한 픽셀 자체를 흐리게 하면(2배 확대 시 둘째 칸을 평균) 획 두께가 1px 인
       글꼴에서는 **획 절반이 회색 줄** 이 된다. 원본은 획 안이 꽉 차 있고
       바깥에만 흐린 픽셀이 있다(044 `状` 의 세로획 = 흐림·195·245·220·흐림).
    원본 실측(001 `状`): 획 하나가 `230 115` — 반 픽셀은 «가로 방향, 획 바깥» 에만
    붙고 세로에는 없다. 그래서 배수와 무관하게 «복제 → 오른쪽 바깥에 반 픽셀» 로 통일한다.
    """
    dup = [bits[i // xscale] for i in range(len(bits) * xscale)]
    out = [0.0] * (len(dup) + (1 if aa else 0))
    for k, v in enumerate(dup):
        if v:
            out[k] = 1.0
    if aa:
        for k in range(len(out)):
            if out[k] == 0.0 and k > 0 and dup[k - 1]:
                out[k] = 0.5           # 획 «바깥» 에만. 획 안을 건드리면 회색 줄이 생긴다.
    return out


def draw_text(a, font, text, x, y, w, h, budget, cols, align="l", xscale=1, kern="", dx=0,
              aa=True, mode="t", yscale=1, dy=0, valign="c", outline=0):
    glyphs = []
    for ch in text:
        b = font.bitmap(ch)
        if b is None:
            raise SystemExit("폰트에 없는 문자: %r" % ch)
        glyphs.append(b)
    kd = [0] * len(glyphs)
    for part in (kern or "").split(","):
        part = part.strip()
        if part:
            i, v = part.split(":")
            kd[int(i)] = int(v)
    total = sum(b["dwidth"] * xscale + k for b, k in zip(glyphs, kd))
    # 정렬에 따라 «쓸 수 있는 구간» 이 다르다. r 은 상자 오른끝에 맞추므로 왼쪽으로 뻗는다.
    if align == "r":
        lo, room = x + w - total, x + w
    elif align == "m":
        # 가운데 정렬은 상자 밖으로 «양쪽» 뻗을 수 있다. 한계는 옆 라벨까지의 여유가
        # 아니라 텍스처 폭 — 원문보다 긴 한글도 좌우 대칭으로 넘칠 수 있어야 한다.
        c = x + w / 2.0
        lo, room = x, int(2 * min(c, a.shape[1] - c))
    else:
        lo, room = x, budget
    if total > room:
        raise SystemExit("폭 초과: %r → %d px > 여유 %d px" % (text, total, room))
    if align == "c":
        lo = x + (budget - total) // 2
    elif align == "m":
        # ★원문 «잉크 상자» 기준 가운데. c 는 다음 라벨까지의 여유 기준이라
        #   좌우 2열 배치(EVENT 003)에서는 오른쪽으로 크게 밀린다.
        lo = x + (w - total) // 2
        hi = lo + total
    hi = lo + total
    # 세로 정렬 — 잉크 덩어리를 상자 안에 가운데로. BDF 의 y 는 «베이스라인 기준 밑변».
    ascent = max(b["y"] + b["h"] for b in glyphs) * yscale
    descent = min(b["y"] for b in glyphs) * yscale
    if valign == "t":
        # ★상자 «위»에 붙인다. 게임이 라벨의 첫 행을 안 그리는 화면에서
        #   가운데 정렬을 쓰면 상자 높이에 따라 글자가 1px 씩 내려가 들쭉날쭉해진다.
        baseline = y + dy + ascent
    else:
        baseline = y + (h - (ascent - descent)) // 2 + ascent + dy
    # ① 커버리지 맵부터 만든다. 색을 바로 찍으면 가장자리를 알 수 없어 안티를 못 건다.
    H, W = a.shape[:2]
    cov = np.zeros((H, W), np.float32)
    cx = lo + dx
    for b, k in zip(glyphs, kd):
        cx += k // 2                       # 넓힌 폭의 절반을 앞에 둬 글자를 가운데로
        top = baseline - (b["y"] + b["h"]) * yscale
        for ry, row in enumerate(b["rows"]):
            rc = row_coverage(row, xscale, aa)
            for s in range(yscale):          # 세로 배수 — 22px 표지판 글꼴처럼 큰 칸용
                gy = top + ry * yscale + s
                if not 0 <= gy - y < h or not 0 <= gy < H:
                    continue
                for rx, v in enumerate(rc):
                    if v <= 0:
                        continue
                    gx = cx + b["x"] * xscale + rx
                    if 0 <= gx < W and lo + dx <= gx <= hi + dx:
                        cov[gy, gx] = max(cov[gy, gx], v)
        cx += b["dwidth"] * xscale + k - k // 2

    # ② 합성. 안티 픽셀은 «검정과 섞은 불투명 픽셀» 이다(알파가 1비트뿐이므로).
    #    배경 그림 위(mode k)에서는 검정이 아니라 그 자리의 배경색과 섞는다.
    # ★검은 테두리 — 원문 글자가 테두리를 두르고 있으면 한글도 둘러야 배경 위에서 읽힌다.
    #   안티(반투명 회색)와 다르다. 획 «바깥 8방향» 에 불투명 검정을 깐다.
    if outline:
        ink = cov > 0.05
        big = ink.copy()
        for oy in (-1, 0, 1):
            for ox in (-1, 0, 1):
                big |= np.roll(np.roll(ink, oy, 0), ox, 1)
        edge = big & ~ink
        a[..., :3][edge] = 0
        a[..., 3][edge] = 255
    ys, xs = np.nonzero(cov > 0.05)
    for gy, gx in zip(ys.tolist(), xs.tolist()):
        f = float(cov[gy, gx])
        c = np.array(cols[max(0, min(h - 1, gy - y))], np.float32)
        if mode == "k" and a[gy, gx, 3] > 32:
            base = a[gy, gx, :3].astype(np.float32)
        else:
            base = np.zeros(3, np.float32)
        a[gy, gx, :3] = np.rint(base * (1 - f) + c * f).astype(np.uint8)
        a[gy, gx, 3] = 255


def main():
    tex, tsv, out = sys.argv[1], sys.argv[2], sys.argv[3]
    base = os.path.basename(tex)
    bgrgb = (0, 255, 0) if base.startswith(("043", "044")) else (0, 0, 0)
    a0 = np.asarray(Image.open(tex).convert("RGBA"))
    a = a0.copy()
    cache = {}
    lines = [l for l in open(tsv, encoding="utf-8").read().splitlines() if l.strip()]
    head = lines[0].split("\t")
    cleared, n, jobs = [], 0, []
    for line in lines[1:]:
        r = dict(zip(head, line.split("\t")))
        if not r.get("ko", "").strip():
            continue
        mode = r.get("mode", "t") or "t"
        ink = ink_of(a0, mode)
        x0, y0, w0, h0 = (int(r[k]) for k in ("x", "y", "w", "h"))
        if (r.get("fit", "1") or "1") == "0":
            # ★잉크에 맞추지 «않는» 칸. 격자 아틀라스(CHAR 000)처럼 «칸» 자체가
            #   의미를 갖는 경우 — 원문이 「ー」 처럼 2px 짜리면 상자가 그만큼
            #   찌그러져 한글을 아예 못 그린다.
            x, y, w, h = x0, y0, w0, h0
        else:
            x, y, w, h = tight_box(ink, x0, y0, w0, h0)
        if (x, y, w, h) != (x0, y0, w0, h0):
            print("  상자 보정 %s: %d,%d %dx%d → %d,%d %dx%d"
                  % (r["ja"], x0, y0, w0, h0, x, y, w, h))
        fk = r.get("font", "n") or "n"
        if fk not in cache:
            cache[fk] = BDF(os.path.join(FONTDIR, FONTS[fk]))
        jobs.append((r, mode, ink, x, y, w, h, fk,
                     row_colors(a0, ink, x, y, w, h),
                     avail_width(ink, x, y, w, h)))

    # ★★ 지우기를 «전부 먼저» 한다. 행마다 «지우고 그리고» 를 반복하면
    #    두 줄짜리 라벨에서 아랫줄의 지우기가 윗줄에 그린 글자의 아랫부분을 지운다
    #    (D2 표지판 「약속의 땅 / 디아볼로스」 에서 윗줄 밑이 잘렸다).
    for r, mode, ink, x, y, w, h, fk, cols, bud in jobs:
        erase(a, a0, ink, x, y, w, h, bgrgb, mode)
    for r, mode, ink, x, y, w, h, fk, cols, bud in jobs:
        if r["ko"] == "-":                 # 지우기만 하고 아무것도 안 그리는 칸
            cleared.append((x, y, w, h, mode))
            n += 1
            continue
        draw_text(a, cache[fk], r["ko"], x, y, w, h, bud, cols,
                  r.get("align", "l") or "l", int(r.get("xscale") or 1),
                  r.get("kern", ""), int(r.get("dx") or 0),
                  (r.get("aa", "1") or "1") != "0", mode,
                  int(r.get("yscale") or 1), int(r.get("dy") or 0),
                  r.get("valign", "c") or "c", int(r.get("outline") or 0))
        cleared.append((x, y, w, h, mode))
        n += 1

    # 검산 — 라벨 «바로 옆» 에 원문 획이 한 줄이라도 남으면 한글 옆에 점으로 찍힌다.
    done = np.zeros(a0.shape[:2], bool)
    for x, y, w, h, _ in cleared:
        done[y:y + h, x:x + w] = True
    rest = np.zeros(a0.shape[:2], bool)
    for x, y, w, h, mode in cleared:
        win = np.zeros(a0.shape[:2], bool)
        win[max(0, y - 2):y + h + 2, max(0, x - 2):x + w + 2] = True
        rest |= ink_of(a0, mode) & win & ~done      # 마스크는 상자마다 다르다
    ys, xs = np.nonzero(rest)
    if len(ys):
        print("★ 상자 밖에 남은 원문 잉크 %d px: %s"
              % (len(ys), sorted(set(zip(xs.tolist(), ys.tolist())))[:10]))
    else:
        print("검산: 라벨 주변에 남은 원문 잉크 없음 ✅")
    Image.fromarray(a).save(out)
    print("%d개 라벨 반영 → %s  (배경 RGB %s)" % (n, out, bgrgb))


if __name__ == "__main__":
    main()

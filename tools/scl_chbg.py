# -*- coding: utf-8 -*-
r"""마법진 장 제목 카드 바탕 복원(2026-10-31) → work/scl_bg/red.npy · teal.npy (텍스처 해상도 RGB 640×240) + 미리보기 my files/그래픽미리보기/마법진_바탕_*.png
  1) 빨강 11장(디스크1 118~133 · 디스크2 31~43)은 바탕이 같은 그림 — 카드마다 글자 화소(검은 테 + 그 둘레 밝은 회색 채움)를 빼고
     다른 카드의 같은 자리 값으로 채움(가장 많은 카드가 같은 값)
  2) 청록 «最終章»(디스크2 46)은 같은 그림의 색만 다른 판(밝기 상관 0.98, 어긋남 0) — 빨강 구멍은 청록 화소를, 청록 구멍은 빨강 화소를
     색 대응표(양쪽 다 글자 없는 화소에서 «청록 565 값 → 빨강 평균»)로 바꿔 채움 · 표에 없는 색은 가까운 색
  3) 그래도 남은 화소(양쪽 모두 글자) = 주변 칠하기(cv2.inpaint)
  python tools/scl_chbg.py"""
import os, sys
import numpy as np, cv2
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import scl_draw as D, scl_ko as K

RED = ['disc1_EVENT_%d' % n for n in (118, 121, 124, 127, 130, 133)] + ['disc2_EVENT_%d' % n for n in (31, 34, 37, 40, 43)]
TEAL = 'disc2_EVENT_46'
BOX = (66, 174, 80, 560)
DIL = int(os.environ.get("CHBG_DIL", 3))                                # 글자 판정 넓힘(5·7 은 구멍이 커져 오히려 얼룩 — 3 이 가장 나음, 2026-10-31 비교)
GLYPH_Y, GLYPH_X = (60, 106), ((158, 244), (398, 484))                  # 第·章(모든 판 같은 자리) 텍스처 범위                                                # 글자가 있는 텍스처 범위(y0,y1,x0,x1)


def text_mask(rgb, exclude):
    r = rgb.astype(int); mx = r.max(2); sat = mx - r.min(2)
    box = np.zeros(mx.shape, bool); y0, y1, x0, x1 = BOX; box[y0:y1, x0:x1] = True
    dark = (mx < 50) & (sat < 35) & box & ~exclude
    near = cv2.dilate(dark.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
    light = (sat < 45) & (mx > 140) & near
    t = cv2.morphologyEx((dark | light).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    return (cv2.dilate(t, np.ones((DIL, DIL), np.uint8)) > 0) & ~exclude


def color_map(src, dst, ok):
    """src 565 값 → dst RGB 평균(ok 화소에서), 없는 값은 가장 가까운 src 색"""
    keys = src[ok]; vals = dst[ok].astype(float)
    u, inv = np.unique(keys, return_inverse=True)
    sums = np.zeros((len(u), 3)); np.add.at(sums, inv, vals); cnt = np.bincount(inv)
    lut = sums / cnt[:, None]; urgb = K.to_rgb(u[None])[0].astype(float)

    def apply(vals565):
        out = np.zeros(vals565.shape + (3,))
        pos = np.searchsorted(u, vals565); pos = np.clip(pos, 0, len(u) - 1)
        hit = u[pos] == vals565
        out[hit] = lut[pos[hit]]
        if (~hit).any():
            q = K.to_rgb(vals565[~hit][None])[0].astype(float)
            nn = np.argmin(((q[:, None, :] - urgb[None]) ** 2).sum(2), 1)
            out[~hit] = lut[nn]
        return np.clip(out + 0.5, 0, 255).astype(np.uint8)
    return apply


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    A = np.stack([D.load(k)[1]['screen'] for k in RED]); n = len(RED)
    same = (A == A[0]).all(0)
    TM = np.stack([text_mask(K.to_rgb(a), same) for a in A])
    best = np.zeros(A.shape[1:], int); red = A[0].copy()
    for i in range(n):
        c = ((A == A[i]) & ~TM).sum(0); up = ~TM[i] & (c > best); best[up] = c[up]; red[up] = A[i][up]
    rhole = best == 0
    teal = D.load(TEAL)[1]['screen']; thole = text_mask(K.to_rgb(teal), np.zeros_like(same))
    ok = ~rhole & ~thole
    t2r = color_map(teal, K.to_rgb(red), ok); r2t = color_map(red, K.to_rgb(teal), ok)
    R = K.to_rgb(red); Tt = K.to_rgb(teal)
    f = rhole & ~thole; R[f] = t2r(teal[f])
    g = thole & ~rhole; Tt[g] = r2t(red[g])
    both = rhole & thole
    print('빨강 구멍 %d (청록에서 %d) · 청록 구멍 %d (빨강에서 %d) · 둘 다 %d' % (rhole.sum(), f.sum(), thole.sum(), g.sum(), both.sum()))
    # 4) 모든 판에서 같은 자리 글자(第·章 — 11장 모두 같은 화소라 1) 의 판정에서 빠짐): 검은 테 둘레까지 넓혀
    #    마법진 180° 맞은편(텍스처 위아래·좌우 뒤집기, 중심 320,120) 화소로 — 육각별·원은 180° 대칭
    y0, y1, x0, x1 = BOX; box = np.zeros(same.shape, bool); box[y0:y1, x0:x1] = True
    gb = np.zeros(same.shape, bool)
    for gx0, gx1 in GLYPH_X: gb[GLYPH_Y[0]:GLYPH_Y[1], gx0:gx1] = True     # 第·章 자리만
    glyph = text_mask(K.to_rgb(A[0]), np.zeros_like(same)) & gb
    both = both | glyph
    both = cv2.dilate(both.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    # 육각별·원의 대칭(180° · 위아래 · 좌우)으로 채우되, 구멍 덩어리마다 «둘레 원래 화소»가 가장 잘 맞는 이동(±4)을 따로 찾음
    #   (2026-10-31 하스피: 통째 뒤집기는 선이 1~3화소 어긋나 깨짐 — 세로 절반 텍스처라 화소 단위 대칭이 아님)
    def rot_disp(ang, flip):
        """표시 공간(세로 2배)에서 중심(320,240) 회전 후 텍스처로 — 육각별은 60° 대칭"""
        M = cv2.getRotationMatrix2D((319.5, 239.5), ang, 1)
        def f(a):
            b = a[:, ::-1] if flip else a
            big = cv2.resize(b.astype(np.float32), (640, 480), interpolation=cv2.INTER_NEAREST)
            r = cv2.warpAffine(big, M, (640, 480), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            r = cv2.resize(r, (640, 240), interpolation=cv2.INTER_AREA)
            return (r > 0.5) if a.dtype == bool else (np.clip(r + 0.5, 0, 255).astype(a.dtype) if a.dtype == np.uint8 else r)
        return f
    # 하스피 2026-10-31: 육각별은 위아래 완전 대칭 → 위아래 접기(1화소 내려 맞춤)를 먼저, 바깥 이중원(글씨 비대칭)은 접지 않음
    cy_ring = np.zeros(same.shape, bool); yy, xx = np.mgrid[0:240, 0:640]
    rr = np.hypot((xx - 320) / 1.0, (yy - 120) * 2.0)                     # 표시 공간 반지름
    inner = rr < 198                                                     # 이중원(안쪽 선 반지름 202) 안쪽 = 육각별·안쪽 고리
    flipy = lambda a: np.roll(a[::-1, :], 1, 0)
    # 어느 카드에서든 글자가 닿았던 화소(되살린 값에 테 찌꺼기가 섞일 수 있음)는 «더러움» — 접은 맞은편이 깨끗하면 맞은편 원본으로
    filled = 0
    for _ in range(2):                                                   # 맞은편이 구멍 아니면 접어서(접어 채운 화소가 다음 원천)
        ok2 = both & inner & ~flipy(both)
        R[ok2] = flipy(R)[ok2]; Tt[ok2] = flipy(Tt)[ok2]; both = both & ~ok2; filled += ok2.sum()
    # 가운데 꽃무늬(반지름 < 75, 표시 공간)는 60° 회전 대칭 — 화소마다 구멍 아닌 회전 원천의 중앙값
    core = both & (rr < 75)
    if core.any():
        vals = []; oks = []
        for ang in (60, 120, 180, 240, 300):
            f = rot_disp(ang, False)
            vals.append(f(R.astype(np.float32))); oks.append(~f(both))
        V = np.stack(vals); O = np.stack(oks)
        med = np.nanmedian(np.where(O[..., None], V, np.nan), 0)
        ok4 = core & ~np.isnan(med[..., 0])
        R[ok4] = np.clip(med[ok4] + 0.5, 0, 255).astype(np.uint8)
        valsT = np.stack([rot_disp(a, False)(Tt.astype(np.float32)) for a in (60, 120, 180, 240, 300)])
        medT = np.nanmedian(np.where(O[..., None], valsT, np.nan), 0)
        Tt[ok4] = np.clip(medT[ok4] + 0.5, 0, 255).astype(np.uint8)
        both = both & ~ok4; filled += ok4.sum()
    left = both
    print('위아래 접기·가운데 회전으로 %d · 남음 %d(주변 칠하기)' % (filled, left.sum()))
    if left.any():
        m = left.astype(np.uint8)
        R = cv2.inpaint(R, m, 2, cv2.INPAINT_TELEA); Tt = cv2.inpaint(Tt, m, 2, cv2.INPAINT_TELEA)
    od = os.path.join(ROOT, 'work', 'scl_bg'); os.makedirs(od, exist_ok=True)
    np.save(os.path.join(od, 'red.npy'), R); np.save(os.path.join(od, 'teal.npy'), Tt)
    pv = os.path.join(ROOT, 'my files', '그래픽미리보기'); os.makedirs(pv, exist_ok=True)
    for name, img, orig in (('빨강', R, A[0]), ('청록', Tt, teal)):
        a = Image.fromarray(K.to_rgb(orig)).resize((640, 480), Image.NEAREST); b = Image.fromarray(img).resize((640, 480), Image.NEAREST)
        s = Image.new('RGB', (1296, 480), (60, 60, 60)); s.paste(a, (0, 0)); s.paste(b, (656, 0)); s.save(os.path.join(pv, '마법진_바탕_%s.png' % name))


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
r"""SCL 화면 읽기·쓰기(2026-10-31) — 타일 지도(tools/scl_screen.py 머리말) 기준, RGB565 원본 값 그대로 다룸
  read(d, p)  → dict(cols, rows, ntex, map, tex=[256×256 u16], pvrt=[텍스처 PVRT 위치], screen=u16[rows*16, cols*16])
  write(d, p, info, new_screen) → d(bytearray) 안 텍스처·지도 고침
     칸마다 새 16×16 조각: 같은 원래 조각을 쓰는 칸들이 모두 같으면 그 조각 제자리에,
     다르면(빈칸 공유 등) 지도가 안 쓰는 조각 자리에 새로 놓고 지도 값 바꿈(같은 내용은 하나로) · 모자라면 중단
  RGB 변환: to_rgb(u16 배열) / from_rgb(RGB 배열) — 그림 그릴 때만, 안 바뀐 화소는 원래 u16 그대로 둘 것
  python tools/scl_ko.py --selftest   → 모든 SCL 을 읽어 그대로 쓰면 바이트 같은지"""
import os, struct, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import scl_screen as S
from twiddle import detwiddle_indices

T = 16
_IDX = np.array(detwiddle_indices(256, 256), np.int64)          # out[y*256+x] = 트위들 저장 순번


def _tex_read(d, k):
    assert d[k:k + 4] == b'PVRT' and d[k + 8] == 1 and d[k + 9] == 1, ('RGB565 트위들만', d[k + 8:k + 10].hex())
    assert struct.unpack_from('<HH', d, k + 12) == (256, 256)
    raw = np.frombuffer(d, '<u2', 256 * 256, k + 16)
    return raw[_IDX].reshape(256, 256).copy()


def _tex_write(d, k, a):
    raw = np.empty(256 * 256, '<u2'); raw[_IDX] = a.reshape(-1)
    d[k + 16:k + 16 + 2 * 256 * 256] = raw.tobytes()


def read(d, p, pv_all=None):
    tsz, ntex, rows, cols = d[p + 8], d[p + 9] & 15, d[p + 10], d[p + 11]
    assert tsz == T
    m = list(struct.unpack_from('<%dI' % (rows * cols), d, p + 0x20))
    pv = [k for k in (pv_all or S.pvrt_index(d)) if k > p][:ntex]
    tex = [_tex_read(d, k) for k in pv]
    scr = np.zeros((rows * T, cols * T), np.uint16)
    for i, v in enumerate(m):
        r, c = divmod(i, cols); t, tx, ty = v >> 16, (v >> 12) & 15, (v >> 4) & 15
        scr[r * T:(r + 1) * T, c * T:(c + 1) * T] = tex[t][ty * T:(ty + 1) * T, tx * T:(tx + 1) * T]
    return dict(p=p, cols=cols, rows=rows, ntex=ntex, map=m, tex=tex, pvrt=pv, screen=scr)


def write(d, info, new):
    cols, m, tex = info['cols'], list(info['map']), [t.copy() for t in info['tex']]
    tiles = lambda i: new[(i // cols) * T:(i // cols + 1) * T, (i % cols) * T:(i % cols + 1) * T]
    get = lambda v: tex[v >> 16][((v >> 4) & 15) * T:((v >> 4) & 15) * T + T, ((v >> 12) & 15) * T:((v >> 12) & 15) * T + T]
    used = set(m)
    free = [(t << 16) | (tx << 12) | (ty << 4) for t in range(info['ntex']) for ty in range(16) for tx in range(16)
            if ((t << 16) | (tx << 12) | (ty << 4)) not in used]
    by = {}
    for i, v in enumerate(m): by.setdefault(v, []).append(i)
    placed = {}                                                          # 새로 놓은 조각 내용 → 지도 값
    newm = list(m); moved = 0
    for v, cells in by.items():
        keep = tiles(cells[0]).tobytes()                                 # 원래 조각 자리 = 첫 칸 내용
        for i in cells:
            b = tiles(i).tobytes()
            if b == keep: continue
            if b in placed: newm[i] = placed[b]; continue
            if not free: raise SystemExit('⛔ 빈 조각 자리 모자람 %X' % info['p'])
            f = free.pop(0); placed[b] = f; newm[i] = f; moved += 1
            get(f)[:] = tiles(i)
        get(v)[:] = tiles(cells[0])
    for k, t in zip(info['pvrt'], tex): _tex_write(d, k, t)
    struct.pack_into('<%dI' % len(newm), d, info['p'] + 0x20, *newm)
    return moved


def to_rgb(a):
    a = a.astype(np.uint32)
    r, g, b = (a >> 11) & 31, (a >> 5) & 63, a & 31
    return np.dstack([(r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2)]).astype(np.uint8)


def from_rgb(rgb):
    rgb = rgb.astype(np.uint32)
    return (((rgb[..., 0] >> 3) << 11) | ((rgb[..., 1] >> 2) << 5) | (rgb[..., 2] >> 3)).astype(np.uint16)


def selftest():
    n = 0
    for disc in ('disc1', 'disc2'):
        for fn in ('EVENT.DAT', 'SYSTEM.DAT'):
            d0 = open(os.path.join(ROOT, 'work', disc, fn), 'rb').read(); d = bytearray(d0); pv = S.pvrt_index(d0)
            for p, *_ in S.scl_blocks(d0):
                try: info = read(d, p, pv)
                except AssertionError: continue
                write(d, info, info['screen']); n += 1
            assert bytes(d) == d0, (disc, fn)
    print('자체 검사 통과 — SCL %d 개 읽고 그대로 쓰기 = 바이트 동일' % n)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if '--selftest' in sys.argv: selftest()

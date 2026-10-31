# -*- coding: utf-8 -*-
r"""`SCL ` 화면 조립(2026-10-31 해독 — 세션3·4 의 «띠 배치 미해결»이 풀림)

SCL 블록 = 타일 지도 + 뒤따르는 PVR 텍스처 n 장
  +0x00 "SCL "  +0x04 0x10000000
  +0x08 u8 타일 크기(16) · u8 하위 4비트 = 텍스처 장수 · u8 줄 수 · u8 열 수   (예 280F2310 = 40열 15줄 텍스처 3장)
  +0x10 0x10 · +0x14 지도 바이트 수
  +0x20 u32 × 열×줄 = 화면 칸(왼→오, 위→아래). 값 = 텍스처 번호 <<16 | 타일 열 <<12 | 타일 줄 <<4
        → 그 텍스처의 (열×16, 줄×16) 16×16 조각. 0x1000 = 빈 조각(텍스처 0 의 (1,0))
  지도 뒤 GBIX/PVRT 텍스처가 차례로(PyPVR 추출 번호 = 파일 안 PVRT 차례)
화면: 40열 15줄 = 640×240 렌더(세로 2배로 640×480 표시) · 40×30 = 640×480
  ⛔옛 가설(16행 띠·4096 스트림·구간 경계)은 이 지도를 몰라 생긴 것 — 지도 하나로 끝

  python tools/scl_screen.py [disc1|disc2] → my files/SCL조립/<디스크>_<파일>_<첫 텍스처 번호>.png"""
import os, struct, sys
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _find_all(d, magic, align):
    out = []; i = d.find(magic)
    while i >= 0:
        if i % align == 0: out.append(i)
        i = d.find(magic, i + 1)
    return out


def scl_blocks(d):
    """[(SCL 위치, 열, 줄, 텍스처 장수, 지도 값 목록)]"""
    out = []
    for p in _find_all(bytes(d), b'SCL ', 16):
        tsz, ntex, rows, cols = d[p + 8], d[p + 9] & 15, d[p + 10], d[p + 11]
        assert tsz == 0x10 or tsz == 0x20, hex(tsz)
        m = struct.unpack_from('<%dI' % (rows * cols), d, p + 0x20)
        out.append((p, cols, rows, ntex, tsz, m))
    return out


def pvrt_index(d):
    return _find_all(bytes(d), b'PVRT', 4)


def compose(cols, rows, tsz, m, tex):
    out = Image.new('RGBA', (cols * tsz, rows * tsz), (0, 0, 0, 0))
    for k, v in enumerate(m):
        r, c = divmod(k, cols); t = v >> 16; ty, tx = (v >> 4) & 0xF, (v >> 12) & 0xF
        if t >= len(tex): continue
        out.alpha_composite(tex[t].crop((tx * tsz, ty * tsz, tx * tsz + tsz, ty * tsz + tsz)), (c * tsz, r * tsz))
    return out


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    discs = [a for a in sys.argv[1:] if a.startswith('disc')] or ['disc1', 'disc2']
    od = os.path.join(ROOT, 'my files', 'SCL조립'); os.makedirs(od, exist_ok=True)
    for disc in discs:
        for fn in ('EVENT.DAT', 'SYSTEM.DAT'):
            d = open(os.path.join(ROOT, 'work', disc, fn), 'rb').read(); pv = pvrt_index(d)
            ext = os.path.join(ROOT, 'work', disc, fn + '_EXT')
            alt = os.path.join(ROOT, 'work', disc, fn + '_ALL', fn + '_EXT')            # 디스크 2 = 전체 추출본(PyPVR -o …_ALL)
            if os.path.isdir(alt): ext = alt
            for p, cols, rows, ntex, tsz, m in scl_blocks(d):
                first = next(i for i, k in enumerate(pv) if k > p)
                tex = [Image.open(os.path.join(ext, '%03d.png' % (first + i))).convert('RGBA') for i in range(ntex)]
                im = compose(cols, rows, tsz, m, tex)
                bg = Image.new('RGBA', im.size, (0, 0, 0, 255)); bg.alpha_composite(im); im = bg.convert('RGB')
                if rows * tsz <= 256: im = im.resize((im.width, im.height * 2), Image.NEAREST)   # 240 줄 렌더 → 표시 2배
                im.save(os.path.join(od, '%s_%s_%03d.png' % (disc, fn.split('.')[0], first)))
            print(disc, fn, len(scl_blocks(d)))


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
r"""「(消費AP3)」 글자 그림 한글화(2026-10-31 하스피 실기 스샷 — 요리할까요？ 뒤 한자)
  이 표시는 문자열이 아니라 그리스 문자 칸에 그려 넣은 글자 그림: Α=「(消」 Β=「費」 Γ=「A」+P 세로획 · Δ~Θ = P 고리 + 숫자1~5 + 「)」
  → Α 의 「(」 는 두고 消 자리에 「소」, Β 에 「모」(Galmuri11 1배 폭 — 원문 한자처럼 좁게) · Γ~Θ 그대로 = 「(소모AP3)」
  SYSTEM.DAT 공통 폰트 청크 — work/build(디스크1)·build2(디스크2) 둘 다
  python tools/build_apcost.py   (build_all_text → build_ui → build_nameentry 다음, build_track3 전 · scl_apply 의 .v07 출발점에도 씀)"""
import os, sys
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import mfdfont as F

FONT = ImageFont.truetype(r'C:\claude\utils\font\Galmuri-v2.40.3\Galmuri11.ttf', 12)


CHARMAP = {l.split('	')[0]: int(l.split('	')[1], 16) for l in open(os.path.join(ROOT, 'work', 'trans', 'charmap.tsv'), encoding='utf-8') if not l.startswith('hangul')}


def ink(ch, d):
    """게임 한글 글꼴(13줄, 가로 2배) 글자를 가로 1배로 — 원문 한자(消費) 크기(13×14)에 맞춤(하스피: Galmuri11 은 너무 작음)"""
    bm = F.read_glyph(d, F.sjis_to_index(CHARMAP[ch]))
    im = Image.new('L', (16, 16), 0)
    for y in range(16):
        for x in range(0, 32, 2):
            if bm[y][x] or bm[y][x + 1]: im.putpixel((x // 2, y), 255)
    return im


def trim(bm):
    """글자 잉크의 맨 왼쪽·맨 오른쪽 열을 1도트씩 지움"""
    cols = [x for x in range(32) if any(bm[y][x] for y in range(16))]
    out = [row[:] for row in bm]
    for y in range(16): out[y][cols[0]] = 0; out[y][cols[-1]] = 0
    return out


def put(bm, im, x0, y0):
    for y in range(im.height):
        for x in range(im.width):
            if im.getpixel((x, y)) > 128:                                  # 가로 2화소(원문 한자 획 굵기 '..')
                for dx in (0, 1):
                    if 0 <= y0 + y < 16 and 0 <= x0 + x + dx < 32: bm[y0 + y][x0 + x + dx] = 1


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    ia = F.sjis_to_index(0x839F); ib = F.sjis_to_index(0x83A0)      # Α Β
    for bd, fn in (('build', 'SYSTEM.DAT'), ('build2', 'SYSTEM.DAT'), ('build', 'SYSTEM.DAT.v07'), ('build2', 'SYSTEM.DAT.v07')):   # .v07 = scl_apply.py 출발점(다시 돌려도 유지)
        p = os.path.join(ROOT, 'work', bd, fn)
        if not os.path.exists(p): continue
        d = bytearray(open(p, 'rb').read())
        a0 = F.read_glyph(open(os.path.join(ROOT, 'work', 'disc1' if bd == 'build' else 'disc2', 'SYSTEM.DAT'), 'rb').read(), ia)   # 「(」는 항상 원본에서(빌드본은 이미 밀려 있음)
        # 하스피: 본문 한글 글꼴 크기 그대로 — Α = 「(」(원래 열 2~7 → 0~5) + 「소」(게임 글꼴 그대로, 열 +4 → 6~31) · Β = 「모」(게임 글꼴 그대로)
        a = [[0] * 32 for _ in range(16)]
        for y in range(16):
            for x in range(2, 9): a[y][x - 2] = a0[y][x]
        so = trim(F.read_glyph(d, F.sjis_to_index(CHARMAP['소']))); mo = trim(F.read_glyph(d, F.sjis_to_index(CHARMAP['모'])))   # 하스피: 양쪽 1도트씩 자름
        for y in range(16):
            for x in range(32):
                if so[y][x] and 0 <= x + 5 < 32: a[y][x + 5] = so[y][x]
        b = [row[:] for row in mo]
        F.write_glyph(d, ia, a); F.write_glyph(d, ib, b)
        open(p, 'wb').write(bytes(d))
        print(bd, fn, 'Α·Β →「(소」「모」')


if __name__ == '__main__':
    main()

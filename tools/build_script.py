# -*- coding: utf-8 -*-
"""대사 빌더 — 추출표(`*_runs.tsv`)를 그대로 되쓴다.

추출표에 **모든 사본 오프셋**이 들어 있으므로 빌더는 검색하지 않는다.
(바이트열 검색은 짧은 문장에서 범위를 넘는다 — 오프닝 빌드에서 `！？` 가 909곳 잡혔다.)

규칙
  · `ko` 가 빈 행은 **건드리지 않는다** → 전 행이 비면 산출물이 원본과 바이트 동일해야 한다
    (`--roundtrip` 로 검증). 이게 통과해야 이 경로를 신뢰할 수 있다.
  · `ko` 길이는 원문 글자 수 이하. 남는 칸은 전각 공백(0x8140)으로 채운다.
  · `{XXXX}` 토큰은 그 코드를 그대로 쓴다(게임 전용 글리프 보존).
  · 한글 음절은 한자 슬롯 앞에서부터 순서대로 배정하고 **배정표를 파일로 남긴다**.
"""
import os
import re
import shutil
import struct
import sys

import mfdfont as F
from hangul_raster import Rasterizer

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = os.path.join(ROOT, "work", "disc1")
BUILD = os.path.join(ROOT, "work", "build")
TRANS = os.path.join(ROOT, "work", "trans")
KANJI_START = 0x889F
TOKEN = re.compile(r"\{([0-9A-Fa-f]{4})\}")


def parse_ko(s):
    """번역문 → 문자 단위 목록. `{XXXX}` 는 코드 정수로."""
    out = []
    i = 0
    while i < len(s):
        m = TOKEN.match(s, i)
        if m:
            out.append(int(m.group(1), 16))
            i = m.end()
        else:
            out.append(s[i])
            i += 1
    return out


def load(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for k, line in enumerate(f):
            if k == 0 or not line.strip():
                continue
            p = line.rstrip("\n").split("\t")
            if len(p) < 6:
                p += [""] * (6 - len(p))
            rows.append(dict(key=p[0], n=int(p[1]), copies=int(p[2]),
                             offs=[int(x, 16) for x in p[3].split(",") if x],
                             ja=p[4], ko=p[5]))
    return rows


def main():
    tsv = sys.argv[1]
    target = sys.argv[2] if len(sys.argv) > 2 else "SCENARIO.DAT"
    roundtrip = "--roundtrip" in sys.argv
    rows = load(tsv)
    todo = [r for r in rows if r["ko"].strip()]
    print("행 %d개 / 번역된 행 %d개" % (len(rows), len(todo)))

    # 1) 음절 수집·배정
    syll = []
    for r in todo:
        for ch in parse_ko(r["ko"]):
            if isinstance(ch, str) and "가" <= ch <= "힣" and ch not in syll:
                syll.append(ch)
    codemap = {}
    code = KANJI_START
    for ch in syll:
        while F.sjis_to_index(code) is None:
            code += 1
        codemap[ch] = code
        code += 1
    print("한글 음절 %d종" % len(syll))
    if syll:
        os.makedirs(TRANS, exist_ok=True)
        with open(os.path.join(TRANS, "charmap.tsv"), "w", encoding="utf-8", newline="") as f:
            f.write("hangul\tsjis\tglyph_index\n")
            for ch, c in codemap.items():
                f.write("%s\t%04X\t%d\n" % (ch, c, F.sjis_to_index(c)))
        print("배정표 → work/trans/charmap.tsv (SJIS %04X~%04X)"
              % (min(codemap.values()), max(codemap.values())))

    # 2) 폰트
    os.makedirs(BUILD, exist_ok=True)
    sysdat = os.path.join(BUILD, "SYSTEM.DAT")
    shutil.copyfile(os.path.join(SRC, "SYSTEM.DAT"), sysdat)
    if syll:
        data = bytearray(open(sysdat, "rb").read())
        r = Rasterizer()
        miss = [ch for ch in syll if r.glyph(ch) is None]
        if miss:
            raise SystemExit("폰트에 없는 음절: %s" % "".join(miss))
        for ch, c in codemap.items():
            F.write_glyph(data, F.sjis_to_index(c), r.glyph(ch))
        open(sysdat, "wb").write(data)
        print("폰트 기록 %d자" % len(syll))

    # 3) 텍스트
    orig = open(os.path.join(SRC, target), "rb").read()
    out = bytearray(orig)
    placed = 0
    for r in todo:
        chars = parse_ko(r["ko"])
        if len(chars) > r["n"]:
            raise SystemExit("[%s] 길이 초과 %d > %d : %s" % (r["key"], len(chars), r["n"], r["ko"]))
        chars += ["　"] * (r["n"] - len(chars))
        buf = bytearray()
        for ch in chars:
            if isinstance(ch, int):
                c = ch
            elif ch in codemap:
                c = codemap[ch]
            else:
                try:
                    b = ch.encode("cp932")
                except Exception:
                    raise SystemExit("[%s] 인코딩 불가: %r" % (r["key"], ch))
                if len(b) != 2:
                    raise SystemExit("[%s] 2바이트가 아님: %r" % (r["key"], ch))
                c = int.from_bytes(b, "big")
                if F.sjis_to_index(c) is None:
                    raise SystemExit("[%s] 폰트에 주소 불가한 코드 %04X (%r)" % (r["key"], c, ch))
            buf += struct.pack("<H", c)
        for o in r["offs"]:
            if out[o:o + len(buf)] != orig[o:o + len(buf)]:
                raise SystemExit("[%s] 0x%X 가 이미 다른 행에 의해 바뀌었다 — 오프셋 충돌" % (r["key"], o))
            out[o:o + len(buf)] = buf
            placed += 1
    dst = os.path.join(BUILD, target)
    open(dst, "wb").write(out)
    print("%s : %d행 / %d곳 반영" % (target, len(todo), placed))

    # 4) 검증
    same = bytes(out) == orig
    if roundtrip:
        print("무변경 왕복 검증:", "✅ 원본과 바이트 동일" if same else "★다름 — 빌더가 무언가를 건드렸다")
        if not same:
            raise SystemExit(1)
    if len(out) != len(orig):
        raise SystemExit("크기가 변했다")
    print("크기 불변 %d" % len(out))


if __name__ == "__main__":
    main()

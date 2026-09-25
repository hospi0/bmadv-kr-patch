# -*- coding: utf-8 -*-
"""전체 텍스트 빌더 — SCENARIO/PARAMETA/1ST_READ 를 **하나의 폰트**로 함께 짓는다.

⚠️★★ 세 파일이 `SYSTEM.DAT` 폰트 청크를 공유한다. `build_script.py` 를 파일별로
   따로 돌리면 그때마다 SYSTEM.DAT 를 원본에서 새로 복사해 «그 파일의 음절만» 같은
   코드 구간(0x889F~)에 배정한다 — 나중 빌드가 앞 빌드의 배정을 덮어써, 이미 지은
   파일의 한글이 «다른 글자»로 나온다. 그래서 여기서는 **모든 대상의 음절을 먼저
   합쳐 한 번만 배정**하고, 그 배정표로 SYSTEM.DAT 와 각 대상 파일을 순서대로 짓는다.

절차
  1) SCENARIO/PARAMETA/1ST_READ 세 표에서 번역된 행의 한글 음절을 모아 **하나의 codemap**.
  2) work/build/SYSTEM.DAT = 원본 복사 + 그 codemap 의 글리프.
  3) 각 대상 파일을 codemap 으로 인코딩해 work/build/ 에 쓴다.
  4) `--roundtrip`: 모든 ko 를 무시하고(마치 전부 빈칸인 것처럼) 원본과 바이트
     동일한지 검증한다. 새 대상(1ST_READ.BIN 등)에 처음 걸 때 반드시 이걸로 먼저 검산.
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

TARGETS = {
    "SCENARIO_text.tsv": "SCENARIO.DAT",
    "PARAMETA_text.tsv": "PARAMETA.DAT",
    "1ST_READ_text.tsv": "1ST_READ.BIN",
}


def parse_ko(s):
    out, i = [], 0
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
            while len(p) < 6:
                p.append("")
            rows.append(dict(key=p[0], n=int(p[1]), copies=int(p[2]),
                             offs=[int(x, 16) for x in p[3].split(",") if x],
                             ja=p[4], ko=p[5]))
    return rows


GROWN = []


def build_target(target, todo, orig_dir, codemap, roundtrip):
    orig = open(os.path.join(orig_dir, target), "rb").read()
    out = bytearray(orig)
    placed = 0
    for r in todo:
        chars = parse_ko(r["ko"])
        if len(chars) > r["n"]:
            raise SystemExit("[%s:%s] 길이 초과 %d > %d : %s" % (target, r["key"], len(chars), r["n"], r["ko"]))
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
                    raise SystemExit("[%s:%s] 인코딩 불가: %r" % (target, r["key"], ch))
                if len(b) != 2:
                    raise SystemExit("[%s:%s] 2바이트가 아님: %r" % (target, r["key"], ch))
                c = int.from_bytes(b, "big")
                if F.sjis_to_index(c) is None:
                    raise SystemExit("[%s:%s] 폰트에 주소 불가한 코드 %04X (%r)" % (target, r["key"], c, ch))
            buf += struct.pack("<H", c)
        # ★★ 문자열 «바로 앞 u16 LE» 는 게임이 그릴 «글자 수» 다.
        #    이걸 안 고치면 번역이 원문보다 길 때 그 수만큼만 그려 «잘린다»
        #    (「木の棒」3 → 「나무막대」4 인데 화면엔 「나무막」).
        #    원본 값이 실제로 그 길이일 때만 손댄다 — 아니면 길이 필드가 아니다.
        core_ja = r["ja"].rstrip("　")
        core_ko = r["ko"].rstrip("　")
        for o in r["offs"]:
            if out[o:o + len(buf)] != orig[o:o + len(buf)]:
                raise SystemExit("[%s:%s] 0x%X 오프셋 충돌" % (target, r["key"], o))
            out[o:o + len(buf)] = buf
            placed += 1
            if o >= 2:
                v = struct.unpack_from("<H", orig, o - 2)[0]
                want = len(parse_ko(core_ko))
                if v == len(core_ja) and v < want <= r["n"]:
                    struct.pack_into("<H", out, o - 2, want)
                    GROWN.append((target, r["key"], core_ja, core_ko, v, want))
    dst = os.path.join(BUILD, target)
    open(dst, "wb").write(out)
    same = bytes(out) == orig
    tag = "✅ 원본과 바이트 동일" if same else ("변경 %d곳" % placed)
    print("%-16s : %5d행 번역 / %5d곳 반영  %s" % (target, len(todo), placed, tag))
    g = [x for x in GROWN if x[0] == target]
    if g:
        print("  ★길이필드(문자열 앞 u16) 늘림 %d곳 — 안 늘리면 화면에서 잘린다" % len(g))
        for _, key, ja, ko, v, want in sorted(set(g))[:40]:
            print("     key %-6s %s(%d) → %s(%d)" % (key, ja, v, ko, want))
    if roundtrip and not same:
        raise SystemExit("[%s] 무변경 왕복 실패 — 빌더가 무언가를 건드렸다" % target)
    if len(out) != len(orig):
        raise SystemExit("[%s] 크기가 변했다" % target)


def main():
    roundtrip = "--roundtrip" in sys.argv
    tsvs = {name: load(os.path.join(TRANS, name)) for name in TARGETS}
    todos = {}
    for name, rows in tsvs.items():
        todos[name] = [] if roundtrip else [r for r in rows if r["ko"].strip()]

    # 1) 전 대상의 한글 음절을 합쳐 한 번만 배정
    syll = []
    for rows in todos.values():
        for r in rows:
            for ch in parse_ko(r["ko"]):
                if isinstance(ch, str) and "가" <= ch <= "힣" and ch not in syll:
                    syll.append(ch)
    # ★이름 입력 화면(NAME 청크)의 음절도 «같은 배정표» 에 넣어야 한다.
    #   따로 배정하면 본문 글리프를 덮어써 대사가 다른 글자로 나온다.
    ne = os.path.join(TRANS, "nameentry.tsv")
    if not roundtrip and os.path.exists(ne):
        for line in open(ne, encoding="utf-8").read().splitlines()[1:]:
            if not line.strip():
                continue
            for ch in line.split("	")[1]:
                if "가" <= ch <= "힣" and ch not in syll:
                    syll.append(ch)
    codemap = {}
    code = KANJI_START
    for ch in syll:
        while F.sjis_to_index(code) is None:
            code += 1
        codemap[ch] = code
        code += 1
    print("한글 음절 %d종 (전 대상 통합)" % len(syll))
    os.makedirs(TRANS, exist_ok=True)
    with open(os.path.join(TRANS, "charmap.tsv"), "w", encoding="utf-8", newline="") as f:
        f.write("hangul\tsjis\tglyph_index\n")
        for ch, c in codemap.items():
            f.write("%s\t%04X\t%d\n" % (ch, c, F.sjis_to_index(c)))
    if syll:
        print("배정표 → work/trans/charmap.tsv (SJIS %04X~%04X)" % (min(codemap.values()), max(codemap.values())))

    # 2) SYSTEM.DAT = 원본 + 통합 폰트
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
        print("SYSTEM.DAT 폰트 기록 %d자" % len(syll))

    # 3) 각 대상 파일
    for name, target in TARGETS.items():
        build_target(target, todos[name], SRC, codemap, roundtrip)

    print("완료 — work/build/ 에 SYSTEM.DAT + %s" % ", ".join(TARGETS.values()))


if __name__ == "__main__":
    main()

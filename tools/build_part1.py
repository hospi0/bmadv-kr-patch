# -*- coding: utf-8 -*-
"""파트1 한글화 빌드 — 폰트 글리프 기록 + 대사 재인코딩.

입력  work/trans/part1_ko.tsv   (idx, off, len, ja, ko)
출력  work/build/SYSTEM.DAT     (한글 글리프가 들어간 폰트)
      work/build/SCENARIO.DAT   (한글로 바뀐 대사)
      work/trans/part1_charmap.tsv  ← ★배정표. 빌드마다 남긴다.

방침(사용자 지시): 전면 한글화가 목표이므로 «아직 안 쓰는 코드만 고르기»는 하지 않는다.
한자 구간 앞에서부터 순서대로 배정한다. 미번역 구간이 깨지는 것은 감수한다.

원문 그대로 두는 문자(기호·전각공백)는 배정 대상이 아니다.
"""
import collections
import os
import shutil
import struct
import sys

import mfdfont as F
from hangul_raster import Rasterizer

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = os.path.join(ROOT, "work", "disc1")
BUILD = os.path.join(ROOT, "work", "build")
TRANS = os.path.join(ROOT, "work", "trans")
KANJI_START = 0x889F          # 한자 구간 시작 — 여기부터 순서대로 배정


def load_rows():
    rows = []
    with open(os.path.join(TRANS, "part1_ko.tsv"), encoding="utf-8") as f:
        for k, line in enumerate(f):
            if k == 0 or not line.strip():
                continue
            p = line.rstrip("\n").split("\t")
            if len(p) < 5:
                continue
            rows.append(dict(idx=int(p[0]), off=int(p[1], 16), n=int(p[2]), ja=p[3], ko=p[4]))
    return rows


def swap16(text, codemap):
    """문자열 → 디스크 바이트열(u16 LE = SJIS 빅엔디언 뒤집기)."""
    out = bytearray()
    for ch in text:
        if ch in codemap:
            code = codemap[ch]
        else:
            try:
                code = int.from_bytes(ch.encode("cp932"), "big")
            except Exception:
                raise SystemExit("인코딩 불가 문자: %r" % ch)
            if len(ch.encode("cp932")) != 2:
                raise SystemExit("2바이트가 아닌 문자: %r" % ch)
        out += struct.pack("<H", code)
    return bytes(out)


def main():
    rows = load_rows()
    # 1) 필요한 한글 음절 수집 (등장 순서 고정 → 재현 가능)
    syllables = []
    for r in rows:
        for ch in r["ko"]:
            if "가" <= ch <= "힣" and ch not in syllables:
                syllables.append(ch)
    print("한글 음절 %d종" % len(syllables))

    # 2) 배정 — 한자 구간 앞에서부터
    codemap = {}
    code = KANJI_START
    for ch in syllables:
        while F.sjis_to_index(code) is None:
            code += 1
        codemap[ch] = code
        code += 1
    os.makedirs(TRANS, exist_ok=True)
    with open(os.path.join(TRANS, "part1_charmap.tsv"), "w", encoding="utf-8", newline="") as f:
        f.write("hangul\tsjis\tglyph_index\n")
        for ch, c in codemap.items():
            f.write("%s\t%04X\t%d\n" % (ch, c, F.sjis_to_index(c)))
    print("배정표 → work/trans/part1_charmap.tsv  (SJIS %04X~%04X)"
          % (min(codemap.values()), max(codemap.values())))

    # 3) 폰트에 글리프 기록
    os.makedirs(BUILD, exist_ok=True)
    sysdat = os.path.join(BUILD, "SYSTEM.DAT")
    shutil.copyfile(os.path.join(SRC, "SYSTEM.DAT"), sysdat)
    data = bytearray(open(sysdat, "rb").read())
    r = Rasterizer()
    missing = []
    for ch, c in codemap.items():
        g = r.glyph(ch)
        if g is None:
            missing.append(ch)
            continue
        F.write_glyph(data, F.sjis_to_index(c), g)
    if missing:
        raise SystemExit("폰트에 없는 음절: %s" % "".join(missing))
    open(sysdat, "wb").write(data)
    print("폰트 기록 %d자 → work/build/SYSTEM.DAT" % len(codemap))

    # 4) 대사 재인코딩 — 같은 원문이 여러 사본에 있으면 «전부» 바꾼다
    scn = os.path.join(BUILD, "SCENARIO.DAT")
    shutil.copyfile(os.path.join(SRC, "SCENARIO.DAT"), scn)
    sdata = bytearray(open(scn, "rb").read())
    orig = open(os.path.join(SRC, "SCENARIO.DAT"), "rb").read()

    # ⚠️ 짧은 문장(`！？` 등)은 스크립트 전역에 흩어져 있어 «맹목적 전역 치환»을 하면
    #    범위 밖까지 바뀐다(실제로 909곳이 잡혔다). 그래서 «블록 단위»로 겨냥한다:
    #    블록마다 긴 앵커 문장의 사본 위치를 찾아 델타를 구하고,
    #    그 델타로 각 줄의 위치를 계산한 뒤 **원본 바이트가 실제로 그 자리에 있는지 확인**하고 쓴다.
    BLOCKS = [("독백", range(0, 21), 5), ("여주인공", range(21, 26), 24)]

    def find_all(pat):
        out = []
        i = orig.find(pat)
        while i >= 0:
            out.append(i)
            i = orig.find(pat, i + 1)
        return out

    by_idx = {r["idx"]: r for r in rows}
    total_hits = 0
    for bname, rng, anchor_idx in BLOCKS:
        a = by_idx[anchor_idx]
        a_bytes = orig[a["off"]:a["off"] + a["n"] * 2]
        anchors = find_all(a_bytes)
        if not anchors:
            raise SystemExit("%s 블록 앵커를 못 찾음" % bname)
        deltas = [x - a["off"] for x in anchors]
        # 블록 창: 이 블록 줄들이 놓인 범위 + 여유. 사본마다 내부 배치가 조금씩 다르므로
        # «균일 델타»를 가정하지 않고 창 안에서 검색한다.
        lo = min(by_idx[i]["off"] for i in rng)
        hi = max(by_idx[i]["off"] + by_idx[i]["n"] * 2 for i in rng)
        # ⚠️ 여유값은 «사본 간격보다 작아야» 한다. 사본이 0x1000 간격인데 여유를 0x1000 으로
        #    주면 창이 겹쳐 같은 자리를 여러 번 센다(실제로 6곳이 14곳으로 부풀었다).
        MARGIN = 0x100
        print("  [%s] 블록 사본 %d개 (델타 %s), 창 0x%X~0x%X"
              % (bname, len(deltas), ["0x%X" % d for d in deltas], lo, hi))
        for i in rng:
            row = by_idx[i]
            # ⚠️ 원문은 «파일에서 그대로» 읽는다 — cp932 재인코딩은 게임 전용
            #    글리프(痺=0x825C, 躰=0x827D)를 다른 코드로 바꿔 못 찾게 만든다.
            ja_bytes = orig[row["off"]:row["off"] + row["n"] * 2]
            ko = row["ko"]
            if len(ko) > row["n"]:
                raise SystemExit("[%d] 길이 초과 %d > %d" % (row["idx"], len(ko), row["n"]))
            ko_bytes = swap16(ko + "　" * (row["n"] - len(ko)), codemap)
            assert len(ko_bytes) == len(ja_bytes), "길이 불변이 깨졌다"
            if ko_bytes == ja_bytes:
                # 안 바뀌는 줄(`！？`·`・・・？？）` 등)은 건드리지 않는다.
                # 짧아서 다른 문장 안에도 들어 있어 오히려 위험하다.
                print("     [%2d] 변경 없음 — 건너뜀  %s" % (row["idx"], ko))
                continue
            done = 0
            for d in deltas:
                w0 = max(0, lo + d - MARGIN)
                w1 = min(len(orig), hi + d + MARGIN)
                j = orig.find(ja_bytes, w0, w1)
                while j >= 0:
                    if j % 2:
                        raise SystemExit("[%d] 홀수 오프셋 0x%X" % (row["idx"], j))
                    sdata[j:j + len(ko_bytes)] = ko_bytes
                    done += 1
                    j = orig.find(ja_bytes, j + 1, w1)
            if done == 0:
                raise SystemExit("[%d] 블록 창 안에서 원문을 못 찾음: %s" % (row["idx"], row["ja"]))
            total_hits += done
            print("     [%2d] %d곳  %s" % (row["idx"], done, ko))
    open(scn, "wb").write(sdata)
    print("대사 %d줄 / 사본 합계 %d곳 → work/build/SCENARIO.DAT" % (len(rows), total_hits))

    # 5) 크기 불변 검증
    for name in ("SYSTEM.DAT", "SCENARIO.DAT"):
        a = os.path.getsize(os.path.join(SRC, name))
        b = os.path.getsize(os.path.join(BUILD, name))
        print("  %s 크기 %d → %d %s" % (name, a, b, "OK" if a == b else "★변함"))
        if a != b:
            raise SystemExit("크기가 변했다")


if __name__ == "__main__":
    main()

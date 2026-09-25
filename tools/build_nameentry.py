# -*- coding: utf-8 -*-
"""이름 입력 화면(`SYSTEM.DAT` 의 `NAME` 청크)을 한글로 바꾼다.

구조 (u16 LE 개수 + 그 수만큼의 문자, 문자는 swap16 SJIS)
    0x1CD6B0  90  히라가나 표   → 한글 표1
    0x1CD770  90  가타카나 표   → 한글 표2
    0x1CD830  90  영숫자 표     → 그대로
    0x1CD8F0  11  버튼(2자×5 + ＿)
    0x1CD9B0~ 기본 이름 9개 : u16 LE 길이 + 7자 고정, 레코드 16 B

★ 화면 배치는 «5자 묶음» 이 한 줄의 좌/우 블록으로 번갈아 들어가 9행 × 10열이 된다.
  따라서 표 문자열을 그냥 순서대로 넣으면 좌→우, 위→아래로 읽힌다.
⛔ 버튼은 «2자 고정 5개». 3자 라벨은 못 넣는다(칸 수 11 고정).
⛔ 이름칸은 7자 고정. 남는 칸은 전각 공백으로 채운다.
★ 한글 코드는 반드시 `build_all_text.py` 가 만든 charmap 을 쓴다 —
  따로 배정하면 본문 글리프를 덮어써 대사가 깨진다.
"""
import os
import struct
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = os.path.join(ROOT, "work", "disc1")
BUILD = os.path.join(ROOT, "work", "build")
TRANS = os.path.join(ROOT, "work", "trans")

TAB1, TAB2, TAB3, BTN = 0x1CD6B0, 0x1CD770, 0x1CD830, 0x1CD8F0
NAMES = 0x1CD9B0
NAME_LEN = 7


def load_map():
    m = {}
    for k, line in enumerate(open(os.path.join(TRANS, "charmap.tsv"), encoding="utf-8")):
        if k == 0 or not line.strip():
            continue
        ch, sj, _ = line.rstrip("\n").split("\t")
        m[ch] = int(sj, 16)
    return m


def code(ch, cmap):
    if ch in cmap:
        return cmap[ch]
    b = ch.encode("cp932")
    if len(b) != 2:
        raise SystemExit("2바이트가 아님: %r" % ch)
    return int.from_bytes(b, "big")


def put(data, off, text, cmap, expect):
    n = struct.unpack_from("<H", data, off)[0]
    if n != expect:
        raise SystemExit("0x%X 칸 수가 %d — %d 이어야 한다" % (off, n, expect))
    if len(text) != expect:
        raise SystemExit("0x%X 글자 수가 %d — %d 이어야 한다" % (off, len(text), expect))
    for i, ch in enumerate(text):
        struct.pack_into("<H", data, off + 2 + i * 2, code(ch, cmap))


def main():
    rows = [l.rstrip("\n").split("\t") for l in
            open(os.path.join(TRANS, "nameentry.tsv"), encoding="utf-8").read().split("\n")
            if l.strip()][1:]
    d = {"table1": None, "table2": None, "buttons": None}
    names = []
    for kind, text in rows:
        if kind == "name":
            names.append(text)
        else:
            d[kind] = text

    target = os.path.join(BUILD, "SYSTEM.DAT")
    if not os.path.exists(target):
        raise SystemExit("work/build/SYSTEM.DAT 이 없다 — build_all_text.py 를 먼저")
    data = bytearray(open(target, "rb").read())
    orig_len = len(data)
    cmap = load_map()

    put(data, TAB1, d["table1"], cmap, 90)
    put(data, TAB2, d["table2"], cmap, 90)
    put(data, BTN, d["buttons"], cmap, 11)
    print("  표1·표2 각 90칸, 버튼 11칸 기록 (영숫자 표는 그대로)")

    o = NAMES
    for i, nm in enumerate(names):
        if len(nm) > NAME_LEN:
            raise SystemExit("이름 %r 이 %d자 — %d자 이하여야 한다" % (nm, len(nm), NAME_LEN))
        struct.pack_into("<H", data, o, len(nm))
        for j, ch in enumerate((nm + "　" * NAME_LEN)[:NAME_LEN]):
            struct.pack_into("<H", data, o + 2 + j * 2, code(ch, cmap))
        print("  기본이름 #%d %-8s len=%d @0x%X" % (i, nm, len(nm), o))
        o += 16

    if len(data) != orig_len:
        raise SystemExit("크기가 변했다")
    open(target, "wb").write(data)
    print("SYSTEM.DAT : %d B (크기 불변), 이름 입력 화면 한글화" % len(data))


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""디스크 2용 빌드 — SYSTEM.DAT / EVENT.DAT.

★ 디스크 2는 대사 3파일(SCENARIO·PARAMETA·1ST_READ)이 디스크 1과 **바이트 동일**이라
  work/build/ 의 결과물을 그대로 쓰면 된다. SYSTEM.DAT 도 폰트(MFD)·이름입력(NAME)
  청크가 바이트 동일이라 같은 코드로 쓰지만, **메뉴 UI 텍스처 오프셋만 다르다**.
  EVENT.DAT 는 파일 자체가 달라 표지판 인덱스도 다르다(D1 093~117 ↔ D2 007~030).

⛔ PVR 은 131,088 B 고정. 크기가 바뀌면 부팅 불가.
"""
import os
import shutil
import subprocess
import sys

import mfdfont as F
from hangul_raster import Rasterizer

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC1 = os.path.join(ROOT, "work", "disc1")
SRC2 = os.path.join(ROOT, "work", "disc2")
BUILD = os.path.join(ROOT, "work", "build")
BUILD2 = os.path.join(ROOT, "work", "build2")
TRANS = os.path.join(ROOT, "work", "trans")
KO = os.path.join(ROOT, "my files", "한글화")
PYPVR = r"C:\claude\utils\dreamcast\PyPVR\pypvr.py"
TMP = r"C:\claude\pvrtmp3"
PVR_SIZE = 131088

# 메뉴 UI 텍스처 : D2 SYSTEM.DAT 안의 오프셋 (내용은 D1 과 동일한 그림)
UI_D2 = {"001": 0x21890, "042": 0x5BC010, "043": 0x5DCCD0, "044": 0x5FCCF0}
# 표지판 : D2 EVENT.DAT 텍스처 인덱스
SIGNS_D2 = list(range(7, 31))


def pvrt_offsets(data):
    o, i = [], -1
    while True:
        i = data.find(b"PVRT", i + 1)
        if i < 0:
            return o
        o.append(i)


def encode(png, tag):
    shutil.copyfile(png, os.path.join(TMP, tag + ".png"))
    subprocess.run([sys.executable, PYPVR, tag + ".png", "-tw", "-1555"],
                   cwd=TMP, capture_output=True)
    out = os.path.join(TMP, tag + ".PVR")
    if not os.path.exists(out):
        raise SystemExit("인코딩 실패: %s" % png)
    d = open(out, "rb").read()
    if len(d) != PVR_SIZE:
        raise SystemExit("%s 크기 %d — %d 이어야 한다" % (tag, len(d), PVR_SIZE))
    return d


def build_system():
    """D1 빌드본의 «폰트·NAME 청크» 를 D2 원본에 옮기고, UI 텍스처를 D2 오프셋에 넣는다."""
    o1 = open(os.path.join(SRC1, "SYSTEM.DAT"), "rb").read()
    b1 = open(os.path.join(BUILD, "SYSTEM.DAT"), "rb").read()
    o2 = open(os.path.join(SRC2, "SYSTEM.DAT"), "rb").read()
    d = bytearray(o2)
    # 폰트(MFD) + 이름입력(NAME) — 두 디스크가 바이트 동일한 구간만 통째로 옮긴다
    for lo, hi, name in ((0x424E0, 0xD2500, "폰트"), (0x1CD6A0, 0x1CDA60, "이름입력")):
        if o1[lo:hi] != o2[lo:hi]:
            raise SystemExit("%s 구간이 두 디스크에서 다르다 — 중단" % name)
        d[lo:hi] = b1[lo:hi]
        print("  %s 청크 0x%X~0x%X 이식" % (name, lo, hi))
    for tag, off in sorted(UI_D2.items()):
        ko = encode(os.path.join(ROOT, "work", "ui", "%s_ko.png" % tag), "k" + tag)
        if len(o2[off:off + PVR_SIZE]) != PVR_SIZE:
            raise SystemExit("%s 오프셋이 파일 끝을 넘는다" % tag)
        d[off:off + PVR_SIZE] = ko
        print("  UI %s → 0x%X" % (tag, off))
    if len(d) != len(o2):
        raise SystemExit("크기가 변했다")
    open(os.path.join(BUILD2, "SYSTEM.DAT"), "wb").write(d)
    print("SYSTEM.DAT(D2) : %d B (크기 불변)" % len(d))


def build_event():
    orig = open(os.path.join(SRC2, "EVENT.DAT"), "rb").read()
    offs = pvrt_offsets(orig)
    d = bytearray(orig)
    ext = os.path.join(SRC2, "EVENT.DAT_EXT")
    for n in SIGNS_D2:
        png = os.path.join(KO, "d2_event%03d_ko.png" % n)
        if not os.path.exists(png):
            print("  %03d 한글본 없음 — 건너뜀" % n)
            continue
        off = offs[n]
        chk = encode(os.path.join(ext, "%03d.png" % n), "o%03d" % n)
        if chk != orig[off:off + PVR_SIZE]:
            raise SystemExit("%03d : 원본 재인코딩이 디스크와 다르다 — 중단" % n)
        ko = encode(png, "k%03d" % n)
        diff = sum(1 for x, y in zip(ko, orig[off:off + PVR_SIZE]) if x != y)
        d[off:off + PVR_SIZE] = ko
        print("  %03d → 0x%X (무손실 검산 ✅, 바뀐 바이트 %d)" % (n, off, diff))
    if len(d) != len(orig):
        raise SystemExit("크기가 변했다")
    open(os.path.join(BUILD2, "EVENT.DAT"), "wb").write(d)
    print("EVENT.DAT(D2) : %d B (크기 불변)" % len(d))


def main():
    os.makedirs(BUILD2, exist_ok=True)
    os.makedirs(TMP, exist_ok=True)
    try:
        build_system()
        build_event()
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    # 대사 3파일은 두 디스크가 동일 — 빌드본을 그대로 쓴다
    for f in ("SCENARIO.DAT", "PARAMETA.DAT", "1ST_READ.BIN", "CHAR.DAT"):
        if open(os.path.join(SRC1, f), "rb").read() != open(os.path.join(SRC2, f), "rb").read():
            raise SystemExit("%s 가 두 디스크에서 다르다 — 중단" % f)
        shutil.copyfile(os.path.join(BUILD, f), os.path.join(BUILD2, f))
        print("  %s 는 두 디스크 동일 → 빌드본 복사" % f)


if __name__ == "__main__":
    main()

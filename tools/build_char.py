# -*- coding: utf-8 -*-
"""한글화한 `CHAR.DAT` 텍스처를 제자리에 끼워 넣는다(전투 UI 글자 아틀라스 000).

build_event.py 와 같은 규약 — PVR 은 **131,088 B 고정**, 크기가 바뀌면 부팅 불가.
원본 PNG 를 다시 인코딩해 디스크 바이트와 같은지 먼저 검산한다.
디스크 1·2 의 CHAR.DAT 는 바이트 동일하므로 결과물을 그대로 양쪽에 쓴다.
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = os.path.join(ROOT, "work", "disc1")
EXT = os.path.join(SRC, "CHAR.DAT_EXT")
BUILD = os.path.join(ROOT, "work", "build")
KO = os.path.join(ROOT, "my files", "한글화")
PYPVR = r"C:\claude\utils\dreamcast\PyPVR\pypvr.py"
TMP = r"C:\claude\pvrtmp3"                 # ⚠️ 대시 없는 경로여야 한다
PVR_SIZE = 131088

JOBS = {"char000_ko.png": 0}


def pvrt_offsets(data):
    offs, i = [], -1
    while True:
        i = data.find(b"PVRT", i + 1)
        if i < 0:
            return offs
        offs.append(i)


def encode(png, tag):
    shutil.copyfile(png, os.path.join(TMP, tag + ".png"))
    subprocess.run([sys.executable, PYPVR, tag + ".png", "-tw", "-1555"],
                   cwd=TMP, capture_output=True)
    out = os.path.join(TMP, tag + ".PVR")
    if not os.path.exists(out):
        raise SystemExit("인코딩 실패: %s" % png)
    data = open(out, "rb").read()
    if len(data) != PVR_SIZE:
        raise SystemExit("%s 크기 %d — %d 이어야 한다" % (tag, len(data), PVR_SIZE))
    return data


def main():
    os.makedirs(TMP, exist_ok=True)
    os.makedirs(BUILD, exist_ok=True)
    orig = open(os.path.join(SRC, "CHAR.DAT"), "rb").read()
    offs = pvrt_offsets(orig)
    target = os.path.join(BUILD, "CHAR.DAT")
    if not os.path.exists(target):
        shutil.copyfile(os.path.join(SRC, "CHAR.DAT"), target)
        print("work/build/CHAR.DAT 새로 복사")
    data = bytearray(open(target, "rb").read())
    if len(data) != len(orig):
        raise SystemExit("빌드본 크기가 원본과 다르다")

    todo = [(f, n) for f, n in sorted(JOBS.items(), key=lambda t: t[1])
            if os.path.exists(os.path.join(KO, f))]
    print("대상 %d장" % len(todo))
    try:
        for f, n in todo:
            off = offs[n]
            enc = encode(os.path.join(EXT, "%03d.png" % n), "o%03d" % n)
            if enc != orig[off:off + PVR_SIZE]:
                raise SystemExit("%03d : 원본 재인코딩이 디스크와 다르다 — 중단" % n)
            ko = encode(os.path.join(KO, f), "k%03d" % n)
            diff = sum(1 for x, y in zip(ko, orig[off:off + PVR_SIZE]) if x != y)
            data[off:off + PVR_SIZE] = ko
            print("  %03d → 0x%X 반영 (무손실 검산 ✅, 바뀐 바이트 %d)" % (n, off, diff))
    finally:
        shutil.rmtree(TMP, ignore_errors=True)

    if len(data) != len(orig):
        raise SystemExit("크기가 변했다")
    open(target, "wb").write(data)
    print("CHAR.DAT : %d B (크기 불변), 텍스처 %d장 반영" % (len(data), len(todo)))


if __name__ == "__main__":
    main()

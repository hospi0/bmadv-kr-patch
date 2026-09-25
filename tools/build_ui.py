# -*- coding: utf-8 -*-
"""메뉴 UI 텍스처(한글)를 SYSTEM.DAT 에 끼워 넣는다.

절차
  work/ui/<n>_ko.png  --PyPVR(-tw -1555)-->  <n>.PVR  -->  work/build/SYSTEM.DAT 의 제자리

지켜야 할 것
  · PVR 은 **131,088 B 고정**. 파일 크기가 바뀌면 드림캐스트가 부팅하지 못한다.
  · 오프셋은 PyPVR 이 남긴 `pvr_log.txt` 의 DATA OFFST 값(추출 때 기록된 것).
  · ⚠️ PyPVR 은 경로 안의 `-` 를 «옵션» 으로 읽는다. 프로젝트 경로에 대시가 있으므로
    대시 없는 임시 폴더에서 인코딩하고 끝나면 지운다.
  · 안전 검산: 먼저 «원본 PNG» 를 다시 인코딩해 디스크 바이트와 완전히 같은지 본다.
    이게 통과해야 인코더가 무손실이라는 근거가 생긴다.
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = os.path.join(ROOT, "work", "disc1")
EXT = os.path.join(SRC, "SYSTEM.DAT_EXT")      # 원본에서 뽑아 둔 텍스처 PNG
UI = os.path.join(ROOT, "work", "ui")
BUILD = os.path.join(ROOT, "work", "build")
PYPVR = r"C:\claude\utils\dreamcast\PyPVR\pypvr.py"
TMP = r"C:\claude\pvrtmp"                 # ⚠️ 대시 없는 경로여야 한다
PVR_SIZE = 131088
OFFSETS = {"001": 137360, "042": 6326288, "043": 6460624, "044": 6591728}


def encode(png, tag):
    dst = os.path.join(TMP, tag + ".png")
    shutil.copyfile(png, dst)
    subprocess.run([sys.executable, PYPVR, tag + ".png", "-tw", "-1555"],
                   cwd=TMP, capture_output=True)
    out = os.path.join(TMP, tag + ".PVR")
    if not os.path.exists(out):
        raise SystemExit("인코딩 실패: %s" % png)
    data = open(out, "rb").read()
    if len(data) != PVR_SIZE:
        raise SystemExit("%s 크기가 %d — %d 이어야 한다" % (tag, len(data), PVR_SIZE))
    return data


def main():
    os.makedirs(TMP, exist_ok=True)
    orig = open(os.path.join(SRC, "SYSTEM.DAT"), "rb").read()
    target = os.path.join(BUILD, "SYSTEM.DAT")
    if not os.path.exists(target):
        raise SystemExit("work/build/SYSTEM.DAT 이 없다 — build_part1.py 를 먼저 돌릴 것")
    data = bytearray(open(target, "rb").read())
    if len(data) != len(orig):
        raise SystemExit("빌드본 크기가 원본과 다르다")

    try:
        # ① 무손실 검산 — 원본 PNG 재인코딩이 디스크와 바이트 동일해야 한다
        for tag, off in sorted(OFFSETS.items()):
            enc = encode(os.path.join(EXT, "%s.png" % tag), "o" + tag)
            if enc != orig[off:off + PVR_SIZE]:
                raise SystemExit("%s : 원본 재인코딩이 디스크와 다르다 — 중단" % tag)
            print("  %s 무손실 검산 ✅" % tag)
        # ② 한글본 끼워 넣기
        for tag, off in sorted(OFFSETS.items()):
            ko = encode(os.path.join(UI, "%s_ko.png" % tag), "k" + tag)
            n = sum(1 for x, y in zip(ko, orig[off:off + PVR_SIZE]) if x != y)
            data[off:off + PVR_SIZE] = ko
            print("  %s → 0x%X 반영 (바뀐 바이트 %d)" % (tag, off, n))
    finally:
        shutil.rmtree(TMP, ignore_errors=True)

    if len(data) != len(orig):
        raise SystemExit("크기가 변했다 — 중단")
    open(target, "wb").write(data)
    print("SYSTEM.DAT : %d B (크기 불변), UI 텍스처 %d장 반영" % (len(data), len(OFFSETS)))


if __name__ == "__main__":
    main()

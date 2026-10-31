# -*- coding: utf-8 -*-
"""패치된 파일들을 Track 3 (MODE1/2352) 에 제자리로 써넣는다.

· 파일 크기가 바뀌지 않으므로 ISO 디렉터리·LBA 는 건드리지 않는다.
· 바뀐 바이트가 든 섹터만 고치고, 그 섹터의 **EDC/ECC 를 다시 계산**한다.
· 끝나면 만들어진 트랙에서 파일을 «다시 뽑아» 원본 빌드와 바이트 대조한다.

좌표: track sector index = filesystem LBA - 45000,
      byte offset = index*2352, 유저 데이터는 +16 부터 2048 B.
"""
import os
import shutil
import sys

from cdsector import fix_sector, self_test
from gdi_iso import HIGH_DENSITY_LBA, SECTOR_RAW, USER_LEN, USER_OFF, open_iso, parse_dir

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
BUILD = os.path.join(ROOT, "work", os.environ.get("BMADV_BUILD", "build"))
SRC = os.path.join(ROOT, "work", os.environ.get("BMADV_SRC", "disc1"))


DISC = os.path.basename(SRC)                                            # disc1 / disc2


def pick(base, name, sub):
    """동영상(SFD)은 work/movie/<디스크>(원본) · work/movie/kr/<디스크>(자막) 에 있음(2026-10-31 v0.9)"""
    p = os.path.join(base, name)
    if os.path.exists(p) or not name.upper().endswith(".SFD"):
        return p
    return os.path.join(ROOT, "work", "movie", sub, DISC, name) if sub else os.path.join(ROOT, "work", "movie", DISC, name)


def file_table(track):
    tr, pvd, rl, rn = open_iso(track)
    out = {}
    for name, lba, ln, isdir in parse_dir(tr, rl, rn):
        if not isdir:
            out[name.lstrip("/")] = (lba, ln)
    return out


def main(orig_track, out_track, names):
    print("원본 트랙 : %s" % orig_track)
    print("출력 트랙 : %s" % out_track)
    if not self_test(orig_track):
        raise SystemExit("EDC/ECC 구현 검산 실패 — 중단")

    tbl = file_table(orig_track)
    for n in names:
        if n not in tbl:
            raise SystemExit("ISO 에 %s 가 없다" % n)
        print("  %-14s LBA %-8d %10d B" % (n, tbl[n][0], tbl[n][1]))

    os.makedirs(os.path.dirname(out_track) or ".", exist_ok=True)
    print("복사 중 (1.19 GB)…")
    shutil.copyfile(orig_track, out_track)

    touched = set()
    with open(out_track, "r+b") as f:
        for name in names:
            lba, ln = tbl[name]
            new = open(pick(BUILD, name, "kr"), "rb").read()
            old = open(pick(SRC, name, ""), "rb").read()
            if len(new) != ln or len(old) != ln:
                raise SystemExit("%s 크기 불일치 (ISO %d / 빌드 %d)" % (name, ln, len(new)))
            base = lba - HIGH_DENSITY_LBA
            nsec = (ln + USER_LEN - 1) // USER_LEN
            hit = 0
            for k in range(nsec):
                a = old[k * USER_LEN:(k + 1) * USER_LEN]
                b = new[k * USER_LEN:(k + 1) * USER_LEN]
                if a == b:
                    continue
                pos = (base + k) * SECTOR_RAW
                f.seek(pos)
                sec = bytearray(f.read(SECTOR_RAW))
                sec[USER_OFF:USER_OFF + len(b)] = b
                fix_sector(sec)
                f.seek(pos)
                f.write(sec)
                touched.add(base + k)
                hit += 1
            print("  %-14s 바뀐 섹터 %d개 / 전체 %d" % (name, hit, nsec))
    print("총 %d 섹터 수정 (EDC/ECC 재계산 포함)" % len(touched))

    # 검산 — 만들어진 트랙에서 파일을 다시 뽑아 대조
    print("검산: 산출 트랙에서 파일 재추출 후 대조")
    tr, pvd, rl, rn = open_iso(out_track)
    ok = True
    for name in names:
        lba, ln = tbl[name]
        got = tr.read_bytes(lba, ln)
        want = open(pick(BUILD, name, "kr"), "rb").read()
        same = got == want
        ok &= same
        print("  %-14s %s" % (name, "일치" if same else "★불일치"))
    sz_ok = os.path.getsize(orig_track) == os.path.getsize(out_track)
    print("  트랙 크기 불변: %s (%d)" % (sz_ok, os.path.getsize(out_track)))
    if not (ok and sz_ok):
        raise SystemExit("검산 실패")
    print("✅ 빌드 완료")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3:] or ["SYSTEM.DAT", "SCENARIO.DAT"])

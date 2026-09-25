# -*- coding: utf-8 -*-
"""ISO9660 파일 추출 (원본 무수정, work/ 로만 출력)."""
import os
import sys

from gdi_iso import open_iso, parse_dir


def main(track_path, outdir, names=None, max_size=None):
    tr, pvd, root_lba, root_len = open_iso(track_path)
    entries = parse_dir(tr, root_lba, root_len)
    os.makedirs(outdir, exist_ok=True)
    for name, lba, ln, isdir in entries:
        if isdir:
            continue
        base = name.lstrip("/")
        if names and base not in names:
            continue
        if max_size and ln > max_size:
            continue
        dst = os.path.join(outdir, base)
        with open(dst, "wb") as w:
            remain = ln
            cur = lba
            while remain > 0:
                chunk = tr.read_sector(cur)
                w.write(chunk[:min(len(chunk), remain)])
                remain -= len(chunk)
                cur += 1
        print("%-16s %10d -> %s" % (base, ln, dst))


if __name__ == "__main__":
    track = sys.argv[1]
    outdir = sys.argv[2]
    names = set(sys.argv[3:]) or None
    main(track, outdir, names)

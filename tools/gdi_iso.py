# -*- coding: utf-8 -*-
"""Black-Matrix Advanced (DC) — Track3(MODE1/2352) ISO9660 리더.

좌표 구분(플랫폼 문서 §2):
  - filesystem LBA : ISO9660 디렉터리 레코드가 쓰는 절대 LBA (고밀도 영역 기준 45000 오프셋 포함)
  - track sector index : Track3 파일 내부의 섹터 번호
  - backing-file byte offset : track sector index * 2352 (+16 유저데이터)
"""
import struct
import sys

SECTOR_RAW = 2352
USER_OFF = 16
USER_LEN = 2048
HIGH_DENSITY_LBA = 45000  # GD-ROM 고밀도 영역 시작 LBA (Track3 첫 섹터의 filesystem LBA)


class Track:
    def __init__(self, path, base_lba=HIGH_DENSITY_LBA):
        self.f = open(path, "rb")
        self.f.seek(0, 2)
        self.size = self.f.tell()
        self.nsectors = self.size // SECTOR_RAW
        self.base_lba = base_lba

    def read_sector(self, lba):
        """filesystem LBA -> 2048B 유저 데이터"""
        idx = lba - self.base_lba
        if idx < 0 or idx >= self.nsectors:
            raise IndexError("LBA %d out of track (idx %d / %d)" % (lba, idx, self.nsectors))
        self.f.seek(idx * SECTOR_RAW + USER_OFF)
        return self.f.read(USER_LEN)

    def read_bytes(self, lba, length):
        out = bytearray()
        while len(out) < length:
            out += self.read_sector(lba)
            lba += 1
        return bytes(out[:length])


def both_endian32(b):
    return struct.unpack("<I", b[:4])[0]


def parse_dir(track, lba, length, path="/", out=None, seen=None):
    if out is None:
        out = []
    if seen is None:
        seen = set()
    if lba in seen:
        return out
    seen.add(lba)
    data = track.read_bytes(lba, length)
    pos = 0
    while pos < len(data):
        rec_len = data[pos]
        if rec_len == 0:
            # 섹터 나머지는 패딩 -> 다음 섹터 경계로
            pos = (pos // USER_LEN + 1) * USER_LEN
            if pos >= len(data):
                break
            continue
        rec = data[pos:pos + rec_len]
        ext_lba = both_endian32(rec[2:10])
        ext_len = both_endian32(rec[10:18])
        flags = rec[25]
        name_len = rec[32]
        name = rec[33:33 + name_len]
        pos += rec_len
        if name_len == 1 and name in (b"\x00", b"\x01"):
            continue
        nm = name.decode("ascii", "replace")
        if nm.endswith(";1"):
            nm = nm[:-2]
        full = path + nm
        if flags & 0x02:
            out.append((full + "/", ext_lba, ext_len, True))
            parse_dir(track, ext_lba, ext_len, full + "/", out, seen)
        else:
            out.append((full, ext_lba, ext_len, False))
    return out


def open_iso(path):
    tr = Track(path)
    # PVD: filesystem LBA 45000+16
    pvd = tr.read_sector(tr.base_lba + 16)
    assert pvd[1:6] == b"CD001", pvd[:16]
    root = pvd[156:156 + 34]
    root_lba = both_endian32(root[2:10])
    root_len = both_endian32(root[10:18])
    return tr, pvd, root_lba, root_len


if __name__ == "__main__":
    tr, pvd, root_lba, root_len = open_iso(sys.argv[1])
    print("track sectors:", tr.nsectors, "vol:", pvd[40:72].decode("ascii", "replace").strip())
    print("root lba", root_lba, "len", root_len)
    entries = parse_dir(tr, root_lba, root_len)
    total = 0
    for name, lba, ln, isdir in entries:
        if not isdir:
            total += ln
        print("%-40s lba=%-8d size=%-12d %s" % (name, lba, ln, "DIR" if isdir else ""))
    print("files:", sum(1 for e in entries if not e[3]), "total bytes:", total)

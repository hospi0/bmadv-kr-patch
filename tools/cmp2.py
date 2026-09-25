# -*- coding: utf-8 -*-
"""CMP2 컨테이너 파서.

관측된 레이아웃(후보 — 아직 소비 코드로 확정 안 됨):
  0x00  char[4] "CMP2"
  0x04  u32     0x08000040   (전 파일 동일. 의미 미확정)
  0x08  u32     N            엔트리 수
  0x0C  u32[2N] 표. v[2i] = 직전 구획의 섹터 크기, v[2i+1] = 엔트리 i 의 시작 섹터
                 => 엔트리 i 는 섹터 [start_i, start_{i+1}) 를 차지한다.
                    (마지막 엔트리의 끝은 파일 끝)
섹터 = 2048 바이트.

검산: start_0 == 헤더 섹터 수, 마지막 start + 마지막 size == 파일 섹터 수.
"""
import os
import struct
import sys

SECTOR = 2048


class Cmp2:
    def __init__(self, data, name=""):
        assert data[:4] == b"CMP2", data[:4]
        self.name = name
        self.data = data
        self.flag = struct.unpack_from("<I", data, 4)[0]
        self.count = struct.unpack_from("<I", data, 8)[0]
        vals = struct.unpack_from("<%dI" % (self.count * 2), data, 12)
        self.starts = [vals[2 * i + 1] for i in range(self.count)]
        self.sizes_field = [vals[2 * i] for i in range(self.count)]
        self.header_sectors = self.sizes_field[0]
        total_sectors = len(data) // SECTOR
        self.ranges = []
        for i in range(self.count):
            s = self.starts[i]
            e = self.starts[i + 1] if i + 1 < self.count else total_sectors
            self.ranges.append((s, e))
        # 검산
        self.consistent = all(
            self.sizes_field[i] == self.starts[i] - self.starts[i - 1]
            for i in range(1, self.count)
        ) and self.starts[0] == self.header_sectors

    def entry(self, i):
        s, e = self.ranges[i]
        return self.data[s * SECTOR:e * SECTOR]


def load(path):
    return Cmp2(open(path, "rb").read(), os.path.basename(path))


if __name__ == "__main__":
    for path in sys.argv[1:]:
        c = load(path)
        tot = len(c.data) // SECTOR
        print("%-14s flag=%08X count=%-5d hdr_sectors=%-3d total_sectors=%-6d consistent=%s"
              % (c.name, c.flag, c.count, c.header_sectors, tot, c.consistent))
        szs = [(e - s) for s, e in c.ranges]
        print("   entry sectors: min=%d max=%d sum=%d (+hdr %d = %d)"
              % (min(szs), max(szs), sum(szs), c.header_sectors, sum(szs) + c.header_sectors))

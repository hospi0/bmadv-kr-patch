# -*- coding: utf-8 -*-
"""`SCL ` / `PVX ` 블록 파서.

관측(§5 갱신):
  SCL  +0x00 magic "SCL "
       +0x04 u32 0x10000000
       +0x08 u32 **TCW 계열 서술자** (예 0x280F2310)
                 bit31 mip / bit30 scan(0=트위들) / bit29..27 픽셀포맷
                 (5=4bpp팔레트 6=8bpp팔레트 0=1555 1=565 2=4444)
                 bit26 VQ / bit25..21 팔레트선택 / bit20..0 주소(8B 단위)
       +0x0C u32 0
       +0x10 u32 n
       +0x14 u32 m
       +0x20 부터 u32 오프셋 표
  PVX  +0x00 magic "PVX ", +0x04 u32 0x11000000, +0x10 u32 n, +0x14 u32 m,
       +0x18 u32 k, +0x70 부터 8바이트 레코드
"""
import struct

FMT = {0: "ARGB1555", 1: "RGB565", 2: "ARGB4444", 3: "YUV422",
       4: "Bump", 5: "4BPP_PAL", 6: "8BPP_PAL", 7: "resv"}


def decode_tcw(t):
    return dict(raw=t, addr=(t & 0x1FFFFF) * 8, pal=(t >> 21) & 0x1F,
                vq=(t >> 26) & 1, fmt=FMT[(t >> 27) & 7],
                twiddled=not ((t >> 30) & 1), mip=(t >> 31) & 1)


def parse_scl(d, off=0):
    assert d[off:off + 4] == b"SCL ", d[off:off + 4]
    f = struct.unpack_from("<8I", d, off + 4)
    return dict(magic="SCL ", w1=f[0], tcw=decode_tcw(f[1]), z=f[2],
                n=f[3], m=f[4], rest=f[5:],
                offs=list(struct.unpack_from("<%dI" % max(1, min(f[3], 64)), d, off + 0x20)))


def parse_pvx(d, off=0):
    assert d[off:off + 4] == b"PVX ", d[off:off + 4]
    f = struct.unpack_from("<8I", d, off + 4)
    return dict(magic="PVX ", w1=f[0], n=f[3], m=f[4], k=f[5])


def walk_pac(d, off=0):
    """PAC 하위 블록 (오프셋 기준 off+0x20)."""
    assert d[off:off + 4] == b"PAC "
    n = struct.unpack_from("<I", d, off + 8)[0]
    total = struct.unpack_from("<I", d, off + 12)[0]
    base = off + 0x20
    offs = list(struct.unpack_from("<%dI" % n, d, base))
    ends = offs[1:] + [total]
    return [(base + a, b - a) for a, b in zip(offs, ends)]

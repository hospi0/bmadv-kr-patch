# -*- coding: utf-8 -*-
"""바이트 구간을 PNG 로 렌더한다 (외부 의존 없음, stdlib zlib 만).

모드:
  1bpp / 2bpp / 4bpp / 8bpp  — 인덱스 값을 회색조로 (팔레트 미지정 시)
  rgb565 / argb1555 / argb4444 — 16비트 픽셀 (리틀엔디언 u16)
"""
import struct
import sys
import zlib


def write_png(path, w, h, rgb_rows):
    raw = bytearray()
    for row in rgb_rows:
        raw.append(0)
        raw += row
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    png += chunk(b"IEND", b"")
    open(path, "wb").write(png)


def rows_indexed(data, w, h, bpp):
    ppb = 8 // bpp
    stride = w // ppb
    maxv = (1 << bpp) - 1
    out = []
    for y in range(h):
        row = bytearray()
        base = y * stride
        for x in range(w):
            b = data[base + x // ppb] if base + x // ppb < len(data) else 0
            if bpp == 8:
                v = b
            else:
                sh = (x % ppb) * bpp
                v = (b >> sh) & maxv
                v = v * 255 // maxv
            row += bytes((v, v, v))
        out.append(row)
    return out


def rows_16(data, w, h, mode):
    out = []
    for y in range(h):
        row = bytearray()
        base = (y * w) * 2
        for x in range(w):
            o = base + x * 2
            p = struct.unpack_from("<H", data, o)[0] if o + 2 <= len(data) else 0
            if mode == "rgb565":
                r = (p >> 11) & 0x1F; g = (p >> 5) & 0x3F; b = p & 0x1F
                row += bytes((r * 255 // 31, g * 255 // 63, b * 255 // 31))
            elif mode == "argb1555":
                r = (p >> 10) & 0x1F; g = (p >> 5) & 0x1F; b = p & 0x1F
                row += bytes((r * 255 // 31, g * 255 // 31, b * 255 // 31))
            else:  # argb4444
                r = (p >> 8) & 0xF; g = (p >> 4) & 0xF; b = p & 0xF
                row += bytes((r * 17, g * 17, b * 17))
        out.append(row)
    return out


def render(data, off, w, h, mode, path):
    if mode.endswith("bpp"):
        bpp = int(mode[:-3])
        need = (w * h) // (8 // bpp)
        rows = rows_indexed(data[off:off + need], w, h, bpp)
    else:
        need = w * h * 2
        rows = rows_16(data[off:off + need], w, h, mode)
    write_png(path, w, h, rows)
    return need


if __name__ == "__main__":
    src, off, w, h, mode, out = sys.argv[1:7]
    data = open(src, "rb").read()
    n = render(data, int(off, 0), int(w), int(h), mode, out)
    print("0x%X +%d B  %sx%s %s -> %s" % (int(off, 0), n, w, h, mode, out))

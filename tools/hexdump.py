# -*- coding: utf-8 -*-
import sys


def dump(data, base=0, width=16):
    for i in range(0, len(data), width):
        row = data[i:i + width]
        hexs = " ".join("%02X" % b for b in row)
        txt = "".join(chr(b) if 0x20 <= b < 0x7F else "." for b in row)
        try:
            sj = row.decode("cp932")
        except Exception:
            sj = ""
        sj = "".join(c if c.isprintable() else "." for c in sj)
        print("%08X  %-*s |%s| %s" % (base + i, width * 3, hexs, txt, sj))


if __name__ == "__main__":
    path = sys.argv[1]
    off = int(sys.argv[2], 0)
    ln = int(sys.argv[3], 0) if len(sys.argv) > 3 else 256
    with open(path, "rb") as f:
        f.seek(off)
        dump(f.read(ln), off)

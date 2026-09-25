# -*- coding: utf-8 -*-
"""CD-ROM MODE1/2352 섹터의 EDC/ECC 계산.

레이아웃
    0x000~0x00B  sync (00 FF×10 00)
    0x00C~0x00F  헤더 (min, sec, frame, mode=01)
    0x010~0x80F  유저 데이터 2048 B
    0x810~0x813  EDC   : 0x000~0x80F 에 대한 CRC (LE)
    0x814~0x81B  0 8 B
    0x81C~0x8C7  ECC P (172 B)
    0x8C8~0x92F  ECC Q (104 B)

⚠️ 유저 데이터를 고치면 EDC/ECC 를 반드시 다시 계산해야 한다.
   구현은 «원본 섹터로 검산»한 뒤에만 쓴다(self_test).
"""
import sys

# ---- EDC ----
_EDC = []
for _i in range(256):
    _e = _i
    for _ in range(8):
        _e = (_e >> 1) ^ (0xD8018001 if _e & 1 else 0)
    _EDC.append(_e & 0xFFFFFFFF)


def edc(data):
    v = 0
    for b in data:
        v = (v >> 8) ^ _EDC[(v ^ b) & 0xFF]
    return v & 0xFFFFFFFF


# ---- ECC ----
_F = [0] * 256
_B = [0] * 256
for _i in range(256):
    _j = ((_i << 1) ^ (0x11D if _i & 0x80 else 0)) & 0xFF
    _F[_i] = _j
    _B[_i ^ _j] = _i


def _block(sec, src_off, major_count, minor_count, major_mult, minor_inc, dest, dest_off):
    # ⚠️ Q 패리티는 «데이터 + P 패리티» 위에서 계산된다(52×43 = 2236 B).
    #    그래서 입력 길이를 major*minor 로 잡아야 하고, P 를 먼저 써넣어야 한다.
    size = major_count * minor_count
    src = sec[src_off:src_off + size]
    for major in range(major_count):
        index = (major >> 1) * major_mult + (major & 1)
        a = 0
        b = 0
        for _ in range(minor_count):
            t = src[index]
            index += minor_inc
            if index >= size:
                index -= size
            a ^= t
            b ^= t
            a = _F[a]
        a = _B[_F[a] ^ b]
        dest[dest_off + major] = a
        dest[dest_off + major + major_count] = a ^ b


def fix_sector(sec):
    """bytearray(2352) 의 EDC/ECC 를 유저 데이터에 맞춰 다시 쓴다."""
    if len(sec) != 2352:
        raise ValueError("섹터는 2352 B 여야 한다")
    v = edc(sec[0x000:0x810])
    sec[0x810] = v & 0xFF
    sec[0x811] = (v >> 8) & 0xFF
    sec[0x812] = (v >> 16) & 0xFF
    sec[0x813] = (v >> 24) & 0xFF
    for i in range(0x814, 0x81C):
        sec[i] = 0
    # P 를 먼저(2064 B = 헤더+데이터+EDC+0), 그다음 Q(2236 B = 위 + P 패리티)
    _block(sec, 0x00C, 86, 24, 2, 86, sec, 0x81C)
    _block(sec, 0x00C, 52, 43, 86, 88, sec, 0x8C8)
    return sec


def self_test(path, sectors=(0, 16, 20, 100, 1000, 50000, 300000)):
    """원본 섹터를 다시 계산해 바이트가 «그대로»인지 확인한다."""
    ok = True
    with open(path, "rb") as f:
        for s in sectors:
            f.seek(s * 2352)
            raw = f.read(2352)
            if len(raw) != 2352:
                continue
            calc = fix_sector(bytearray(raw))
            same = bytes(calc) == raw
            ok &= same
            print("  섹터 %-7d %s" % (s, "일치" if same else "★불일치"))
    print("EDC/ECC 구현 검산:", "통과" if ok else "실패")
    return ok


if __name__ == "__main__":
    sys.exit(0 if self_test(sys.argv[1]) else 1)

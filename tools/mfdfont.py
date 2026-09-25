# -*- coding: utf-8 -*-
"""Black/Matrix Advanced 폰트 코덱 (`MFD` 청크) — 디코더 + 인코더.

확정 사양 (docs/survey.md §18, 코드 0x8C05DD1A / 0x8C05DD2E 에서 읽음):

    청크      SYSTEM.DAT 0x424E0 ~ 0xD2500 (589,856 B), RAM 0x8C75F800 에 그대로 적재
    헤더      "MFD " + u32 → **16 바이트만** 건너뛴다
    글리프    128 B = 2bpp 32×16, PVR 트위들 + (x^1, y^1)
    주소      base + 16 + index*128
    인덱스    0x8140~0x81BF → c+0x7EC0 / 0x8240~0x83BF → c+0x7E40 / 0x889F~0x9872 → c+0x7961
              (전부 16비트 절단)

값(2bpp)은 팔레트 인덱스다. 실기 관측상 **1이 가장 진하고 3이 가장 옅다**(0=투명).
검증: 실기 VRAM 캐시 글리프 6종과 3072/3072 픽셀 일치.
"""
import struct
import sys

CHUNK_OFF = 0x424E0          # SYSTEM.DAT 안에서의 청크 시작
CHUNK_END = 0xD2500
HDR = 16                     # 코드의 `add #16,r0`
GLYPH_BYTES = 128
W, H = 32, 16
NUM_GLYPHS = (CHUNK_END - CHUNK_OFF - HDR) // GLYPH_BYTES   # 4608


def _morton(x, y, bits):
    v = 0
    for i in range(bits):
        v |= ((y >> i) & 1) << (2 * i)
        v |= ((x >> i) & 1) << (2 * i + 1)
    return v


def _build_twiddle():
    """linear index -> 저장 위치. 32×16 은 16×16 정사각 블록 2개."""
    tw = [0] * (W * H)
    for y in range(H):
        for x in range(W):
            tw[y * W + x] = (x // 16) * 256 + _morton(x % 16, y, 4)
    return tw


TWIDDLE = _build_twiddle()
assert sorted(TWIDDLE) == list(range(W * H)), "트위들 표가 순열이 아니다"

# (X,Y) -> 저장 비트 위치.  렌더 시 x^1, y^1 이 적용된다.
POS = [[TWIDDLE[((Y ^ 1) * W) + (X ^ 1)] for X in range(W)] for Y in range(H)]
INV = {}
for _y in range(H):
    for _x in range(W):
        INV[POS[_y][_x]] = (_x, _y)
assert len(INV) == W * H


def sjis_to_index(code):
    """SJIS 2바이트 코드 → 글리프 인덱스. 범위 밖이면 None."""
    if 0x8140 <= code <= 0x81BF:
        return (code + 0x7EC0) & 0xFFFF
    if 0x8240 <= code <= 0x83BF:
        return (code + 0x7E40) & 0xFFFF
    if 0x889F <= code <= 0x9872:
        return (code + 0x7961) & 0xFFFF
    return None


def index_to_sjis(index):
    """글리프 인덱스 → SJIS 코드 (역함수). 없으면 None."""
    for base in (0x7EC0, 0x7E40, 0x7961):
        c = (index - base) & 0xFFFF
        if sjis_to_index(c) == index:
            return c
    return None


def glyph_offset(index):
    """SYSTEM.DAT 안에서의 글리프 시작 오프셋."""
    if not 0 <= index < NUM_GLYPHS:
        raise IndexError("글리프 인덱스 %d 범위 밖 (0~%d)" % (index, NUM_GLYPHS - 1))
    return CHUNK_OFF + HDR + index * GLYPH_BYTES


def decode(raw):
    """128 B → [H][W] 값(0~3)."""
    if len(raw) != GLYPH_BYTES:
        raise ValueError("글리프는 %d B 여야 한다 (받은 값 %d)" % (GLYPH_BYTES, len(raw)))
    out = [[0] * W for _ in range(H)]
    for y in range(H):
        row = out[y]
        prow = POS[y]
        for x in range(W):
            s = prow[x]
            row[x] = (raw[s >> 2] >> (2 * (s & 3))) & 3
    return out


def encode(bitmap):
    """[H][W] 값(0~3) → 128 B."""
    if len(bitmap) != H or any(len(r) != W for r in bitmap):
        raise ValueError("비트맵은 %dx%d 여야 한다" % (W, H))
    raw = bytearray(GLYPH_BYTES)
    for y in range(H):
        prow = POS[y]
        row = bitmap[y]
        for x in range(W):
            v = row[x]
            if not 0 <= v <= 3:
                raise ValueError("픽셀 값은 0~3 이어야 한다 (받은 값 %r)" % (v,))
            s = prow[x]
            raw[s >> 2] |= (v & 3) << (2 * (s & 3))
    return bytes(raw)


def read_glyph(data, index):
    o = glyph_offset(index)
    return decode(data[o:o + GLYPH_BYTES])


def write_glyph(data, index, bitmap):
    """data 는 bytearray. 제자리로 써넣는다(크기 불변)."""
    o = glyph_offset(index)
    data[o:o + GLYPH_BYTES] = encode(bitmap)


def art(bitmap, chars=" .+#"):
    return "\n".join("".join(chars[v] for v in row) for row in bitmap)


def roundtrip(path):
    """전 글리프 디코드→인코드 왕복이 «바이트 동일»인지 검증한다."""
    data = open(path, "rb").read()
    bad = []
    for i in range(NUM_GLYPHS):
        o = glyph_offset(i)
        orig = data[o:o + GLYPH_BYTES]
        if encode(decode(orig)) != orig:
            bad.append(i)
    print("글리프 %d개 왕복 검사 — 불일치 %d개" % (NUM_GLYPHS, len(bad)))
    if bad:
        print("   불일치 인덱스 예:", bad[:20])
        return False
    print("   ✅ 전량 바이트 동일")
    return True


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "roundtrip"
    path = sys.argv[2] if len(sys.argv) > 2 else r"..\work\disc1\SYSTEM.DAT"
    if cmd == "roundtrip":
        sys.exit(0 if roundtrip(path) else 1)
    elif cmd == "show":
        data = open(path, "rb").read()
        for a in sys.argv[3:]:
            if len(a) == 1 and not a.isdigit():
                code = int.from_bytes(a.encode("cp932"), "big")
                i = sjis_to_index(code)
                print("=== %s SJIS 0x%04X → index %d ===" % (a, code, i))
            else:
                i = int(a, 0)
                c = index_to_sjis(i)
                ch = c.to_bytes(2, "big").decode("cp932", "replace") if c else "?"
                print("=== index %d → SJIS %s (%s) ===" % (i, ("0x%04X" % c) if c else "-", ch))
            print(art(read_glyph(data, i)))

# -*- coding: utf-8 -*-
"""PowerVR(드림캐스트) 트위들 텍스처 해제.

트위들 = 모튼 순서. 픽셀 (x,y) 의 저장 인덱스는 x·y 비트를 교차로 끼운 값이며,
드림캐스트는 **y 비트가 하위**(짝수 자리)에 온다.

정사각이 아니면 짧은 쪽 변 길이의 정사각 블록으로 나눠 순서대로 배치한다.
"""


def morton(x, y, bits):
    v = 0
    for i in range(bits):
        v |= ((y >> i) & 1) << (2 * i)
        v |= ((x >> i) & 1) << (2 * i + 1)
    return v


def detwiddle_indices(w, h):
    """반환: out[y*w+x] = 트위들 저장 순서에서의 픽셀 인덱스."""
    side = min(w, h)
    bits = side.bit_length() - 1
    out = [0] * (w * h)
    blocks_x = w // side
    blocks_y = h // side
    for by in range(blocks_y):
        for bx in range(blocks_x):
            base = (by * blocks_x + bx) * side * side
            for y in range(side):
                for x in range(side):
                    out[(by * side + y) * w + (bx * side + x)] = base + morton(x, y, bits)
    return out


def detwiddle_4bpp(data, w, h):
    """4bpp 트위들 → 픽셀 인덱스 바이트열 (w*h)."""
    idx = detwiddle_indices(w, h)
    out = bytearray(w * h)
    for i, src in enumerate(idx):
        byte = data[src >> 1] if (src >> 1) < len(data) else 0
        out[i] = (byte >> 4) & 0xF if (src & 1) else byte & 0xF
    return bytes(out)


def detwiddle_8bpp(data, w, h):
    idx = detwiddle_indices(w, h)
    return bytes(data[s] if s < len(data) else 0 for s in idx)

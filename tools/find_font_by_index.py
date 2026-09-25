# -*- coding: utf-8 -*-
"""«글리프 인덱스»를 열쇠로 고정크기 폰트 표를 찾는다 (인코딩 무관).

우리가 실기에서 확정한 인덱스(§12.2):
    0=　(전각공백, 완전 공백)  1=、  5=・  9=！  41=（  42=）  257=っ  3114=痛
고정 크기 K, 시작 B 인 표라면 블록 i 는 [B+i*K, B+(i+1)*K).

판정(모양이 아니라 «밀도»로):
  - 블록 0 은 전부 0 이어야 한다 (전각 공백)
  - 블록 1·5·9 는 희소 (문장부호)
  - 블록 41·42 는 중간, 257 중간
  - 블록 3114 는 조밀 (痛 = 잉크 158/392)
  - 블록 0 이 0 인데 3114 가 조밀하다 = 강한 신호
"""
import sys

POP = bytes(bin(i).count("1") for i in range(256))

# (인덱스, 기대 밀도 등급) 0=빈칸 1=희소 2=중간 3=조밀
PROBES = [(0, 0), (1, 1), (5, 1), (9, 1), (41, 2), (42, 2), (257, 2), (3114, 3)]
MAXI = max(i for i, _ in PROBES)


def popcount(b):
    return sum(POP[x] for x in b)


def score(data, B, K):
    blocks = {}
    for i, _ in PROBES:
        o = B + i * K
        if o + K > len(data):
            return None
        blocks[i] = data[o:o + K]
    if any(blocks[0]):
        return None                      # 전각 공백이 비어 있지 않으면 탈락
    bits = K * 8
    dens = {i: popcount(blk) / bits for i, blk in blocks.items()}
    if dens[3114] < 0.10:
        return None                      # 痛 가 조밀하지 않으면 탈락
    for i in (1, 5, 9):
        if dens[i] == 0 or dens[i] > dens[3114] * 0.75:
            return None                  # 문장부호가 비었거나 한자만큼 조밀하면 탈락
    # （ 와 ） 는 좌우대칭 → 잉크량이 거의 같아야 한다
    if dens[41] == 0 or dens[42] == 0:
        return None
    r = dens[41] / dens[42]
    if not (0.75 <= r <= 1.34):
        return None
    # 폰트 표라면 1~3114 구간 블록이 «거의 다» 채워져 있어야 한다
    step = 37
    sample = range(1, 3115, step)
    filled = 0
    dsum = 0.0
    n = 0
    for i in sample:
        o = B + i * K
        blk = data[o:o + K]
        p = popcount(blk) / bits
        dsum += p
        n += 1
        if p > 0.005:
            filled += 1
    cov = filled / n
    mean = dsum / n
    if cov < 0.85 or not (0.03 <= mean <= 0.40):
        return None
    return (dens[3114] - max(dens[1], dens[5], dens[9])) * cov


def scan(path, sizes, step=4, top=12):
    data = open(path, "rb").read()
    name = path.split("\\")[-1]
    hits = []
    for K in sizes:
        span = (MAXI + 1) * K
        if span > len(data):
            continue
        for B in range(0, len(data) - span, step):
            s = score(data, B, K)
            if s is not None:
                hits.append((s, B, K))
    hits.sort(reverse=True)
    print("%-14s 후보 %d" % (name, len(hits)))
    for s, B, K in hits[:top]:
        print("     K=%-4d B=0x%08X  점수 %.3f" % (K, B, s))
    return hits


if __name__ == "__main__":
    sizes = [int(x) for x in sys.argv[1].split(",")]
    step = int(sys.argv[2], 0)
    for p in sys.argv[3:]:
        scan(p, sizes, step)

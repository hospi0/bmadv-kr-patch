# -*- coding: utf-8 -*-
"""고정크기 폰트 표를 «포맷 무관» 제약으로 찾는다.

쓰는 제약(전부 비트맵 포맷·팔레트와 무관):
  1. 인덱스 0 = 전각 공백 → 블록이 **완전히 0**
  2. 인덱스 41 `（` 과 42 `）` 는 **좌우대칭** → 잉크(팝카운트)가 **정확히 같다**
     (실기 캐시에서도 둘 다 36으로 일치)
  3. 인덱스 3114 `痛` 는 조밀, 1·5·9 `、・！` 는 희소 → 밀도 순서
  4. 폰트 표는 촘촘하다 → 표본 인덱스의 95% 이상이 비어 있지 않다
"""
import sys

POP = bytes(bin(i).count("1") for i in range(256))
PUNCT = (1, 5, 9)


def pc(b):
    return sum(POP[x] for x in b)


def test(data, B, K, nsample=200):
    n = len(data)
    def blk(i):
        o = B + i * K
        return data[o:o + K] if o + K <= n else None
    b0 = blk(0)
    if b0 is None or any(b0):
        return None
    b41, b42, b3114 = blk(41), blk(42), blk(3114)
    if b41 is None or b42 is None or b3114 is None:
        return None
    p41, p42, p3114 = pc(b41), pc(b42), pc(b3114)
    if p41 == 0 or p42 == 0:
        return None
    if abs(p41 - p42) > 2:            # 대칭쌍 잉크 일치
        return None
    bits = K * 8
    if p3114 / bits < 0.08:
        return None
    for i in PUNCT:
        b = blk(i)
        if b is None:
            return None
        p = pc(b)
        if p == 0 or p >= p3114 * 0.7:
            return None
    # 촘촘함
    filled = 0
    tot = 0
    dsum = 0
    step = max(1, 3114 // nsample)
    for i in range(1, 3115, step):
        b = blk(i)
        if b is None:
            return None
        p = pc(b)
        dsum += p / bits
        tot += 1
        if p > 0:
            filled += 1
    cov = filled / tot
    mean = dsum / tot
    if cov < 0.95 or not (0.02 <= mean <= 0.45):
        return None
    return dict(score=(p3114 / bits) * cov, B=B, K=K, cov=cov, mean=mean,
                p41=p41, p42=p42, p3114=p3114)


def main():
    sizes = [int(x) for x in sys.argv[1].split(",")]
    step = int(sys.argv[2], 0)
    for path in sys.argv[3:]:
        data = open(path, "rb").read()
        name = path.replace("\\", "/").split("/")[-1]
        hits = []
        for K in sizes:
            span = 3115 * K
            if span > len(data):
                continue
            for B in range(0, len(data) - span, step):
                r = test(data, B, K)
                if r:
                    hits.append(r)
        hits.sort(key=lambda r: -r["score"])
        print("%-14s 후보 %d" % (name, len(hits)))
        for r in hits[:10]:
            print("     K=%-4d B=0x%08X  cov=%.3f mean=%.3f  ink(41)=%d ink(42)=%d ink(痛)=%d"
                  % (r["K"], r["B"], r["cov"], r["mean"], r["p41"], r["p42"], r["p3114"]))


if __name__ == "__main__":
    main()

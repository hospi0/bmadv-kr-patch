# -*- coding: utf-8 -*-
"""대사 추출기 — 모집단 열거 + 중복 정리 + 가역 산출물.

방침
  · 텍스트는 u16 LE 워드 스트림. 워드 w 가 «폰트에 주소 가능한 코드»면 글자로 본다
    (`mfdfont.sjis_to_index(w) is not None`). 이게 «SJIS 범위» 보다 엄격하고,
    실제 렌더 가능한 것만 남기므로 오탐이 적다.
  · 제자리 같은 길이 교체가 전제이므로 **제어 토큰을 해석할 필요가 없다.**
    런의 경계만 정확하면 된다.
  · 같은 바이트열이 여러 사본에 있으면 하나의 «키»로 묶고, 반영은 전 사본에 한다.

산출  work/trans/<name>_runs.tsv   (key, len, copies, offsets, ja, ko)
      ko 칸은 비워 둔다. 빌더는 ko 가 빈 행을 건드리지 않는다 → 무변경 왕복이 성립.
"""
import os
import struct
import sys
from collections import OrderedDict

import mfdfont as F

MIN_CHARS = 2


_VALID = None


def _valid_table():
    """65536칸 판정표 — 코드가 폰트에 «주소 가능»한가."""
    global _VALID
    if _VALID is None:
        import numpy as np
        t = np.zeros(65536, dtype=bool)
        for c in range(0x8140, 0x81C0):
            t[c] = True
        for c in range(0x8240, 0x83C0):
            t[c] = True
        for c in range(0x889F, 0x9873):
            t[c] = True
        _VALID = t
    return _VALID


def find_runs(data, min_chars=MIN_CHARS):
    """(offset, nchars) 목록. 글자 워드가 min_chars 개 이상 이어진 구간. (numpy 벡터화)"""
    import numpy as np
    n = len(data) // 2
    words = np.frombuffer(data[:n * 2], dtype="<u2")
    ok = _valid_table()[words]
    d = np.diff(np.concatenate(([False], ok, [False])).astype(np.int8))
    starts = np.flatnonzero(d == 1)
    ends = np.flatnonzero(d == -1)
    lens = ends - starts
    sel = lens >= min_chars
    return [(int(s) * 2, int(l)) for s, l in zip(starts[sel], lens[sel])]


def decode(data, off, nchars, cmap=None):
    out = []
    for j in range(nchars):
        c = struct.unpack_from("<H", data, off + 2 * j)[0]
        if cmap and c in cmap:
            out.append(cmap[c])
            continue
        try:
            out.append(c.to_bytes(2, "big").decode("cp932"))
        except Exception:
            out.append("{%04X}" % c)          # 게임 전용 글리프는 원시 토큰으로 보존
    return "".join(out)


def build_table(path):
    data = open(path, "rb").read()
    runs = find_runs(data)
    groups = OrderedDict()
    for off, n in runs:
        raw = data[off:off + n * 2]
        groups.setdefault(raw, []).append(off)
    return data, runs, groups


def main():
    src = sys.argv[1]
    name = os.path.basename(src).split(".")[0]
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "work", "trans", "%s_runs.tsv" % name)
    data, runs, groups = build_table(src)
    total_chars = sum(n for _, n in runs)
    uniq_chars = sum(len(k) // 2 for k in groups)
    print("%s : 런 %d개 / %d자" % (os.path.basename(src), len(runs), total_chars))
    print("  중복 정리 후 %d개 / %d자  (중복률 %.1f%%)"
          % (len(groups), uniq_chars, 100 * (1 - uniq_chars / total_chars)))
    dist = {}
    for offs in groups.values():
        dist[len(offs)] = dist.get(len(offs), 0) + 1
    print("  사본 수 분포:", dict(sorted(dist.items())[:10]))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="") as f:
        f.write("key\tlen\tcopies\toffsets\tja\tko\n")
        for k, (raw, offs) in enumerate(groups.items()):
            nchars = len(raw) // 2
            ja = decode(data, offs[0], nchars)
            f.write("%d\t%d\t%d\t%s\t%s\t\n"
                    % (k, nchars, len(offs), ",".join("%X" % o for o in offs), ja))
    print("→ %s" % out)


if __name__ == "__main__":
    main()

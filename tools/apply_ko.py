# -*- coding: utf-8 -*-
"""번역 사전(`KO = {key: ko}`)을 추출표의 ko 칸에 채우고 **길이를 검사**한다.

제자리 교체라 ko 글자 수가 원문을 넘으면 빌드가 실패한다. 여기서 미리 잡는다.
`{XXXX}` 토큰은 «한 글자»로 센다(게임 전용 글리프 한 칸).
"""
import importlib.util
import os
import re
import sys

TOKEN = re.compile(r"\{[0-9A-Fa-f]{4}\}")


def nchars(s):
    return len(TOKEN.sub("　", s))


def main():
    tsv, mod = sys.argv[1], sys.argv[2]
    spec = importlib.util.spec_from_file_location("ko", mod)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    KO = m.KO
    lines = open(tsv, encoding="utf-8").read().splitlines()
    head, rows = lines[0], [l for l in lines[1:] if l.strip()]
    out, filled, bad = [], 0, []
    seen = set()
    for l in rows:
        p = l.split("\t")
        while len(p) < 6:
            p.append("")
        k = int(p[0])
        if k in KO:
            ko = KO[k]
            seen.add(k)
            if nchars(ko) > int(p[1]):
                bad.append((k, int(p[1]), nchars(ko), ko))
            p[5] = ko
            filled += 1
        out.append("\t".join(p))
    miss = sorted(set(KO) - seen)
    print("%s : %d행 중 %d행 채움" % (os.path.basename(tsv), len(rows), filled))
    if miss:
        print("  ★사전에는 있는데 표에 없는 key: %s" % miss)
    if bad:
        print("  ★길이 초과 %d건:" % len(bad))
        for k, n, g, ko in bad:
            print("     key=%-5d 예산 %2d < %2d  %s" % (k, n, g, ko))
        raise SystemExit(1)
    open(tsv, "w", encoding="utf-8", newline="").write(head + "\n" + "\n".join(out) + "\n")
    print("  길이 검사 통과 ✅ → %s" % os.path.basename(tsv))


if __name__ == "__main__":
    main()

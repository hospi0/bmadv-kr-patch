# -*- coding: utf-8 -*-
"""사용자가 번역한 SCENARIO 조각 TSV 를 본표에 병합한다.

★ 지켜야 할 것 (전부 과거에 사고가 난 항목)
- **띄어쓰기를 지우지 않는다.** 반각 공백은 «전각 공백으로 바꿀» 뿐, 1:1 대응이다.
- `{XXXX}` 제어 토큰 «안»은 절대 전각화하지 않는다(16진수가 깨진다).
- 이 게임은 전 문자 2바이트 고정 — cp932 로 2바이트 인코딩이 안 되는 글자는 빌드가 깨진다.
  병합 직후 **전수 검사**한다(반각 숫자·`~`·`—`·`-`·홑자음 `ㅠ` 등).
- `・・・` / `...` → `…` 로 통일(자릿수도 벌어준다).
- 예산은 «원문 글자 수»(len 열). 초과분은 사람이 승인한 뒤에만 줄인다.
"""
import io
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
MASTER = os.path.join(ROOT, "work", "trans", "SCENARIO_text.tsv")
TOKEN = re.compile(r"\{[0-9A-Fa-f]{2,6}\}")

FW = {chr(c): chr(c - 0x20 + 0xFF00) for c in range(0x21, 0x7F)}
FW[" "] = "　"
FW["~"] = "～"
FW["—"] = "ー"


def normalize(s):
    """토큰 밖만 전각화. 토큰은 손대지 않는다."""
    out, pos = [], 0
    for m in TOKEN.finditer(s):
        out.append(_fw(s[pos:m.start()]))
        out.append(m.group(0))
        pos = m.end()
    out.append(_fw(s[pos:]))
    return "".join(out)


def _fw(s):
    s = s.replace("・・・", "…").replace("...", "…").replace("・・", "…")
    return "".join(FW.get(ch, ch) for ch in s)


def bad_chars(s):
    """cp932 로 2바이트가 안 되는 글자."""
    bad = []
    for ch in TOKEN.sub("", s):
        try:
            if len(ch.encode("cp932")) != 2:
                bad.append(ch)
        except UnicodeEncodeError:
            bad.append(ch)
    return bad


def cost(s):
    """토큰은 1글자로 센다."""
    return len(TOKEN.sub("\x00", s))


def main():
    rows = [l.split("\t") for l in
            io.open(MASTER, encoding="utf-8").read().split("\n") if l.strip()]
    head, body = rows[0], rows[1:]
    ki, li, ji, koi = head.index("key"), head.index("len"), head.index("ja"), head.index("ko")
    by_key = {r[ki]: r for r in body}

    merged = changed = 0
    over, badc = [], []
    for path in sys.argv[1:]:
        n = 0
        for l in io.open(path, encoding="utf-8").read().split("\n")[1:]:
            if not l.strip():
                continue
            f = l.split("\t")
            if len(f) <= koi or not f[koi].strip():
                continue
            key = f[ki]
            r = by_key.get(key)
            if r is None:
                continue
            ko = normalize(f[koi].strip())
            if r[koi] != ko:
                changed += 1
            r[koi] = ko
            n += 1
            b = bad_chars(ko)
            if b:
                badc.append((key, ko, "".join(sorted(set(b)))))
            if cost(ko) > int(r[li]):
                over.append((key, int(r[li]), cost(ko), r[ji], ko))
        print("  %-16s %d행" % (os.path.basename(path), n))
        merged += n

    io.open(MASTER, "w", encoding="utf-8", newline="").write(
        "\n".join("\t".join(r) for r in [head] + body) + "\n")

    done = sum(1 for r in body if r[koi].strip())
    print("\n병합 %d행(실제 변경 %d) → 번역 완료 %d / %d행 (%.1f%%)"
          % (merged, changed, done, len(body), 100.0 * done / len(body)))
    print("★인코딩 불가 글자 %d행" % len(badc))
    for k, ko, b in badc[:20]:
        print("   key=%s [%s] %s" % (k, b, ko))
    print("★예산 초과 %d행" % len(over))
    for k, bud, c, ja, ko in over[:20]:
        print("   key=%s %d→%d  %s | %s" % (k, bud, c, ja, ko))


if __name__ == "__main__":
    main()

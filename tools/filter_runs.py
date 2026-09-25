# -*- coding: utf-8 -*-
"""추출한 런에서 «진짜 텍스트»만 남긴다.

그래픽 바이트가 우연히 SJIS 로 읽히면 한자가 잔뜩 나온다(`繋繋繋…`).
⚠️ 판정은 **문자열 단위**로 한다 — 파일 전체 비율로 자르면 진짜 텍스트까지 통째로 날아간다.

배제 규칙 (하나라도 걸리면 노이즈)
  · 반복률: 길이 6 이상인데 고유 문자 비율이 낮다 (`繋`×60)
  · 가나 없음: 길이 5 이상인데 히라가나·가타카나가 하나도 없다
  · 미해독 토큰 `{XXXX}` 가 많다 (폰트에 없는 코드 = 데이터)
  · 전각 공백만 잔뜩

⛔ 짧은 문자열(아이템명 등)은 규칙을 느슨하게 — 「剣」「炎」처럼 한자만 있는 정상 이름이 있다.
"""
import os
import re
import sys

TOKEN = re.compile(r"\{[0-9A-Fa-f]{4}\}")


PUNCT = "。、！？「」（）・…～ー：；"


def is_text(s):
    core = TOKEN.sub("", s)
    if not core:
        return False
    ntok = len(TOKEN.findall(s))
    if ntok and ntok * 4 >= len(core):         # 미해독 코드가 본문만큼 많다
        return False
    body = core.replace("　", "").replace(" ", "")
    if not body:
        return False
    kana = sum(1 for c in body if "぀" <= c <= "ヿ")
    uniq = len(set(body)) / len(body)
    if len(body) >= 6 and uniq < 0.34:         # 같은 글자 반복 (`繋`×60)
        return False
    # ★긍정 신호가 «하나라도» 있어야 채택한다. 짧은 한자 나열은 거의 전부 그래픽 바이트다.
    pad = core != core.rstrip("　") and len(body) >= 2      # 전각 공백으로 채운 이름 필드
    punct = any(c in PUNCT for c in core)
    ratio = kana / len(body)
    # ★전각 공백 패딩은 «고정 폭 필드» 의 지문이라 그 자체로 강한 양성 신호다.
    #   가나 비율로 다시 거르면 한자 위주 설명문(「教団御用達の鞭。」)이 통째로 날아간다.
    if pad:
        return True
    # 그 밖에는 가나 «비율» 로 본다. 그래픽 바이트도 가나가 섞이지만 문장처럼 이어지지 않는다.
    if len(body) >= 6:
        return ratio >= 0.35
    return (kana >= 2 and ratio >= 0.4) or (punct and kana >= 1)


def main():
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else src.replace("_runs.tsv", "_text.tsv")
    lines = open(src, encoding="utf-8").read().splitlines()
    head, rows = lines[0], [l for l in lines[1:] if l.strip()]
    keep, chars = [], 0
    for l in rows:
        p = l.split("\t")
        if len(p) >= 5 and is_text(p[4]):
            keep.append(l)
            chars += int(p[1])
    with open(dst, "w", encoding="utf-8", newline="") as f:
        f.write(head + "\n")
        f.write("\n".join(keep) + "\n")
    print("%-22s %6d행 → %6d행 (%5.1f%%), %d자  → %s"
          % (os.path.basename(src), len(rows), len(keep),
             100 * len(keep) / max(1, len(rows)), chars, os.path.basename(dst)))


if __name__ == "__main__":
    main()

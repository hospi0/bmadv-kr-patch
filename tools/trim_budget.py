# -*- coding: utf-8 -*-
"""예산 초과 행을 «사용자가 정한 우선순위»대로 줄인다.

① 마침표(．)·쉼표(，)·말줄임(…) 삭제  — ⛔！？ 는 어조라 절대 지우지 않는다
② 티 안 나는 공백 축약 — 의존명사·보조용언 앞 공백만 붙인다(「뜰까 봐」→「뜰까봐」)
③ 장황한 어미·수식어 축약
④ 그래도 안 되면 일반 공백 축약(티가 나므로 최소한만)

⛔ 공백을 «전부» 지우는 짓은 절대 금지. 한글 가독성이 무너진다.
"""
import io
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
MASTER = os.path.join(ROOT, "work", "trans", "SCENARIO_text.tsv")
TOKEN = re.compile(r"\{[0-9A-Fa-f]{2,6}\}")
SP = "　"

# ② 의존명사·보조용언 — 앞 공백을 붙여도 티가 안 난다
DEP = ("것", "거", "게", "수", "줄", "바", "뿐", "때", "채", "척", "만큼", "만",
       "텐데", "테니", "리", "양", "듯", "법", "체", "김", "적")
AUX = ("있", "없", "보", "주", "버리", "가", "오", "싶", "말", "않", "못", "두", "놓", "대")

# ③ 장황한 어미·수식어 → 짧은 형태 (의미 동일)
PHRASE = [
    ("그러니까", "그럼"), ("아무래도", "암만해도"), ("나중에", "나중"),
    ("말하자면", "말하자면"), ("어차피", "어차피"),
    ("하지만", "허나"), ("그렇지만", "허나"), ("그런데", "헌데"),
    ("왜냐하면", "왜냐면"), ("무엇인가", "뭔가"), ("무엇을", "뭘"),
    ("무엇이", "뭐가"), ("어떻게든", "어떡하든"), ("이렇게", "이리"),
    ("그렇게", "그리"), ("저렇게", "저리"), ("있습니다", "있소"),
    ("것이다", "것"), ("것입니다", "것"), ("하는　것", "할　것"),
]


def cost(s):
    return len(TOKEN.sub("\x00", s))


def cut_punct(s):
    """① 마침표·쉼표·말줄임 하나 지우기. ！？ 는 건드리지 않는다."""
    for ch in ("．", "，", "…"):
        i = s.rfind(ch)
        if i >= 0:
            return s[:i] + s[i + 1:]
    return None


def join_dep(s):
    """② 의존명사·보조용언 앞 공백 하나 붙이기(뒤에서부터)."""
    idx = [m.start() for m in re.finditer(SP, s)]
    for i in reversed(idx):
        tail = s[i + 1:]
        if any(tail.startswith(w) for w in DEP):
            return s[:i] + s[i + 1:]
        if any(tail.startswith(w) for w in AUX) and i > 0 and s[i - 1] in "아어고지야여":
            return s[:i] + s[i + 1:]
    return None


def shorten(s):
    """③ 장황한 표현 축약."""
    for a, b in PHRASE:
        if a in s and len(b) < len(a):
            return s.replace(a, b, 1)
    return None


def join_any(s):
    """④ 일반 공백 하나 붙이기(마지막 수단, 뒤에서부터)."""
    i = s.rfind(SP)
    return s[:i] + s[i + 1:] if i >= 0 else None


def trim(s, budget):
    log = []
    for stage, fn in ((1, cut_punct), (2, join_dep), (3, shorten), (4, join_any)):
        while cost(s) > budget:
            new = fn(s)
            if new is None or new == s:
                break
            s = new
            log.append(stage)
        if cost(s) <= budget:
            break
    return s, log


def main():
    rows = [l.split("\t") for l in
            io.open(MASTER, encoding="utf-8").read().split("\n") if l.strip()]
    h, b = rows[0], rows[1:]
    ki, li, ji, koi = h.index("key"), h.index("len"), h.index("ja"), h.index("ko")
    fixed = 0
    left = []
    stage_cnt = {1: 0, 2: 0, 3: 0, 4: 0}
    for r in b:
        ko = r[koi]
        if not ko.strip():
            continue
        bud = int(r[li])
        if cost(ko) <= bud:
            continue
        new, log = trim(ko, bud)
        for s in log:
            stage_cnt[s] += 1
        if cost(new) <= bud:
            r[koi] = new
            fixed += 1
        else:
            r[koi] = new
            left.append((r[ki], bud, cost(new), r[ji], new))
    io.open(MASTER, "w", encoding="utf-8", newline="").write(
        "\n".join("\t".join(r) for r in [h] + b) + "\n")
    print("해결 %d행 / 남음 %d행" % (fixed, len(left)))
    print("단계별 적용 횟수: ①부호삭제 %d  ②의존명사공백 %d  ③표현축약 %d  ④일반공백 %d"
          % (stage_cnt[1], stage_cnt[2], stage_cnt[3], stage_cnt[4]))
    for k, bud, c, ja, ko in left:
        print("   key=%s %d→%d  %s | %s" % (k, bud, c, ja, ko))


if __name__ == "__main__":
    main()

import collections,re
rows=[l.rstrip("\n").split("\t") for l in open(r"..\work\trans\SCENARIO_runs.tsv",encoding="utf-8")][1:]
rows=[r for r in rows if len(r)>=5]
print("행 %d" % len(rows))
ln=collections.Counter(int(r[1]) for r in rows)
print("길이 분포(짧은 순):", [(k,ln[k]) for k in sorted(ln)[:12]])
print("길이 분포(긴 순):", [(k,ln[k]) for k in sorted(ln)[-6:]])
# 게임 전용 글리프 토큰
tok=collections.Counter()
for r in rows:
    for m in re.findall(r"\{[0-9A-F]{4}\}", r[4]): tok[m]+=1
print("전용 글리프 토큰 %d종:" % len(tok), tok.most_common(10))
# 의심 행: 같은 글자 반복 / 한자만 잔뜩
susp=[r for r in rows if len(set(r[4]))<=2 and int(r[1])>=6]
print("의심(같은 글자 반복) %d행, 예:" % len(susp), [r[4] for r in susp[:6]])
print()
print("=== 표본 (길이 2~3) ===")
for r in [r for r in rows if int(r[1])<=3][:12]: print("  [%s] %s자 x%s  %s" % (r[0],r[1],r[2],r[4]))
print("=== 표본 (중간) ===")
for r in rows[6000:6010]: print("  [%s] %s자 x%s  %s" % (r[0],r[1],r[2],r[4]))

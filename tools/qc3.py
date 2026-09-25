import collections
rows=[l.rstrip("\n").split("\t") for l in open(r"..\work\trans\EVENT_runs.tsv",encoding="utf-8")][1:]
rows=[r for r in rows if len(r)>=5]
def kana(s): return sum(1 for c in s if "\u3040"<=c<="\u30ff")/max(1,len(s))
def tok(s): return s.count("{")/max(1,len(s))
hi=[r for r in rows if kana(r[4])>=0.35 and tok(r[4])==0 and int(r[1])>=5]
print("전체 %d행 / 가나35%%↑·토큰0·5자↑ = %d행 (%.1f%%)" % (len(rows),len(hi),100*len(hi)/len(rows)))
print("그 행들의 글자수 합계: %d" % sum(int(r[1]) for r in hi))
print("\n--- 진짜 대사로 보이는 표본 ---")
for r in hi[:15]: print("  [%s] %s자 x%s  %s" % (r[0],r[1],r[2],r[4][:44]))
print("\n--- 나머지(노이즈 의심) 표본 ---")
lo=[r for r in rows if r not in hi][:0]
import itertools
cnt=0
for r in rows:
    if kana(r[4])>=0.35 and tok(r[4])==0 and int(r[1])>=5: continue
    print("  [%s] %s자 x%s  %s" % (r[0],r[1],r[2],r[4][:44])); cnt+=1
    if cnt>=10: break

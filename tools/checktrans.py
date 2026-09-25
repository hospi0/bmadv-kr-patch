import sys,collections; sys.path.insert(0,".")
import mfdfont as F
rows=[l.rstrip("\n").split("\t") for l in open(r"..\work\trans\part1_ko.tsv",encoding="utf-8")][1:]
bad=[]; syl=collections.Counter(); other=collections.Counter()
print("%-3s %-4s %-4s %s" % ("#","원문","번역",""))
for r in rows:
    if len(r)<5: continue
    i,off,ln,ja,ko=r[0],r[1],int(r[2]),r[3],r[4]
    n=len(ko)
    ok = n<=ln
    if not ok: bad.append((i,n,ln,ko))
    for ch in ko:
        if '가'<=ch<='힣': syl[ch]+=1
        else: other[ch]+=1
    print("[%2s] %2d→%2d %s  %s" % (i,ln,n,"  " if ok else "★초과",ko))
print()
print("길이 초과:", bad if bad else "없음")
print("한글 음절 고유 %d종:" % len(syl), "".join(sorted(syl)))
print("한글 외 문자 %d종:" % len(other), "".join(sorted(other)))
# 한글 외 문자가 전부 원본 폰트에 있는지
miss=[]
for ch in other:
    try: c=int.from_bytes(ch.encode("cp932"),"big")
    except Exception: miss.append(ch); continue
    if F.sjis_to_index(c) is None: miss.append(ch)
print("→ 원본 폰트에 없는 기호:", miss if miss else "없음 (전부 사용 가능)")

import sys; sys.path.insert(0,".")
from swap16_scan import scan
d=open(r"..\work\disc1\SCENARIO.DAT","rb").read()
runs=scan(d,2)
# 목표 범위: 痛っ 부터 思ってた 까지 (첫 사본)
si=None
for k,(off,n,s) in enumerate(runs):
    if "痛っ" in s: si=k; break
ei=None
for k in range(si,len(runs)):
    if "思ってた" in runs[k][2]: ei=k; break
tgt=runs[si:ei+1]
print("범위: 런 %d개, 0x%06X ~ 0x%06X" % (len(tgt),tgt[0][0],tgt[-1][0]+tgt[-1][1]*2))
print("총 글자수 %d" % sum(n for _,n,_ in tgt))
import collections
uniq=collections.Counter()
for _,_,s in tgt:
    for ch in s: uniq[ch]+=1
print("고유 문자 %d종" % len(uniq))
print("  ", "".join(sorted(uniq)))
print()
# 사본 개수: 첫 문장의 바이트열이 몇 번 나오나
def sw(s):
    e=s.encode("cp932"); return bytes(b for i in range(0,len(e),2) for b in (e[i+1],e[i]))
for probe in ("（痛っ・・！）","思ってた！","目を覚まさないんじゃないかと、"):
    p=sw(probe); hits=[]; i=d.find(p)
    while i>=0: hits.append(i); i=d.find(p,i+1)
    print("%-18s 사본 %d개: %s" % (probe,len(hits),["0x%X"%h for h in hits]))

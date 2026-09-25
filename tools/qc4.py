rows=[l.rstrip("\n").split("\t") for l in open(r"..\work\trans\EVENT_runs.tsv",encoding="utf-8")][1:]
rows=[r for r in rows if len(r)>=5]
def kana(s): return sum(1 for c in s if "\u3040"<=c<="\u30ff")/max(1,len(s))
good=[]
for r in rows:
    if kana(r[4])>=0.35 and "{" not in r[4] and int(r[1])>=5:
        for o in r[3].split(","):
            good.append(int(o,16))
good.sort()
# 오프셋 군집
runs=[]
for o in good:
    if runs and o-runs[-1][1]<=0x2000: runs[-1][1]=o
    else: runs.append([o,o])
runs=[(a,b) for a,b in runs if b-a>0x400]
print("신뢰 텍스트가 모인 구간 %d개:" % len(runs))
tot=0
for a,b in sorted(runs,key=lambda x:-(x[1]-x[0]))[:20]:
    print("   0x%08X ~ 0x%08X  (%d KB)" % (a,b,(b-a)//1024)); tot+=b-a
print("합계 %d KB" % (tot//1024))
# 그 구간 안의 «모든» 런 글자수
inreg=0; nrow=0
for r in rows:
    o=int(r[3].split(",")[0],16)
    if any(a-0x1000<=o<=b+0x1000 for a,b in runs):
        inreg+=int(r[1]); nrow+=1
print("구간 안 전체 런: %d행 / %d자" % (nrow,inreg))

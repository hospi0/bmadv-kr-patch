import sys,collections,math; sys.path.insert(0,".")
from cmp2 import load
from scl import walk_pac
def ent(b):
    c=collections.Counter(b); n=len(b)
    return -sum(v/n*math.log2(v/n) for v in c.values())
c=load(r"..\work\disc1\SYSTEM.DAT")
print("바이트 엔트로피 (8.0 만점). 압축/암호화면 7.9 이상이 나온다.")
for i in range(c.count):
    d=c.entry(i)
    if d[:4]==b"PAC ":
        for j,(o,ln) in enumerate(walk_pac(d)):
            s=d[o:o+min(ln,262144)]
            if len(s)<4096: continue
            print("  entry%-2d sub%-2d %-6s len=0x%-8X 엔트로피=%.2f  0비율=%.3f" %
                  (i,j,d[o:o+4].decode('ascii','replace').strip() or "?",ln,ent(s),s.count(0)/len(s)))
    else:
        s=d[:262144]
        if len(s)>=4096:
            print("  entry%-2d       %-6s len=0x%-8X 엔트로피=%.2f  0비율=%.3f" %
                  (i,d[:4].decode('ascii','replace').strip() or "?",len(d),ent(s),s.count(0)/len(s)))

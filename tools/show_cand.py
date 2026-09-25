import sys; sys.path.insert(0,".")
d=open(r"..\work\disc1\SYSTEM.DAT","rb").read()
def art(B,K,i,w=24,h=24,msb=True):
    g=d[B+i*K:B+(i+1)*K]
    out=[]
    for y in range(h):
        r=""
        for x in range(w):
            bit=y*w+x
            v=(g[bit>>3]>>(7-(bit&7)))&1 if msb else (g[bit>>3]>>(bit&7))&1
            r+="##" if v else ".."
        out.append(r)
    return out
NAMES={0:"space",1:"comma",5:"nakaguro",9:"excl",41:"paren-open",42:"paren-close",257:"small-tsu",3114:"itami"}
for B in (0x428A00,0x489400):
    print("############ B=0x%06X K=72 ############" % B)
    for i in (41,42,3114,257):
        print("--- index %d (%s) ---" % (i,NAMES.get(i,"")))
        for r in art(B,72,i): print("   "+r)
        print()

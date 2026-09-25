import sys; sys.path.insert(0,".")
from find_glyph_tex import morton
d=open(r"..\work\disc1\SYSTEM.DAT","rb").read()
CHUNK=0x424E0; HDR=16; K=128
def idx(code):
    if 0x8140<=code<=0x81BF: return (code+0x7EC0)&0xFFFF
    if 0x8240<=code<=0x83BF: return (code+0x7E40)&0xFFFF
    if 0x889F<=code<=0x9872: return (code+0x7961)&0xFFFF
    return code&0xFFFF
def art(i,xlow=False):
    o=CHUNK+HDR+i*K; g=d[o:o+K]
    out=[]
    for y in range(16):
        r=""
        for x in range(32):
            s=morton(x,y,4,xlow)
            v=(g[s>>2]>>(2*(s&3)))&3
            r+=" .+#"[v]
        out.append(r)
    return out
for ch in "痛（）":
    c=int.from_bytes(ch.encode("cp932"),"big"); i=idx(c)
    for xlow in (False,True):
        print("=== %s idx=%d  트위들 %s ===" % (ch,i,"x-low" if xlow else "y-low"))
        for r in art(i,xlow): print("   "+r)
        print()

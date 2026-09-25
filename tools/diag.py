import sys; sys.path.insert(0,".")
from find_glyph_tex import morton
from glyph_extract import glyphs
d=open(r"..\work\disc1\SYSTEM.DAT","rb").read()
sp=r"C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\0b7d618a-9996-40c4-89fe-7ab5b878aad1\scratchpad"
st=open(sp+r"\p1.bin","rb").read()
CHUNK=0x424E0; HDR=16; K=128
def idx(c):
    if 0x8140<=c<=0x81BF: return (c+0x7EC0)&0xFFFF
    if 0x8240<=c<=0x83BF: return (c+0x7E40)&0xFFFF
    if 0x889F<=c<=0x9872: return (c+0x7961)&0xFFFF
    return c&0xFFFF
def src(i,xlow=False):
    o=CHUNK+HDR+i*K; g=d[o:o+K]
    m=[[0]*32 for _ in range(16)]
    for y in range(16):
        for x in range(32):
            s=(x//16)*256+morton(x%16,y,4,xlow)
            m[y][x]=(g[s>>2]>>(2*(s&3)))&3
    return m
cache=glyphs(st,0x0080ABF0,64,64)
for slot,ch in ((2,"痛"),(3,"！"),(0,"（")):
    cm=cache[slot][1]
    s=src(idx(int.from_bytes(ch.encode("cp932"),"big")))
    for dy in (0,-1,1):
        conf={}
        maskmatch=0
        for y in range(14):
            for x in range(28):
                sy=y+dy
                sv=s[sy][x] if 0<=sy<16 else 0
                cv=cm[y][x]
                conf[(sv,cv)]=conf.get((sv,cv),0)+1
                maskmatch += (bool(sv)==bool(cv))
        exact=sum(v for (a,b),v in conf.items() if a==b)
        print("%s dy=%2d  값일치=%3d/392  마스크일치=%3d/392" % (ch,dy,exact,maskmatch))
        if dy==0:
            print("     혼동표 (src→cache):", {k:v for k,v in sorted(conf.items()) if v>3})
    print()

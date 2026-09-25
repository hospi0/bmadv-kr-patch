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
def src(i):
    o=CHUNK+HDR+i*K; g=d[o:o+K]
    m=[[0]*32 for _ in range(16)]
    for y in range(16):
        for x in range(32):
            s=(x//16)*256+morton(x%16,y,4,False)
            m[y][x]=(g[s>>2]>>(2*(s&3)))&3
    return m
cache=glyphs(st,0x0080ABF0,64,64)
pairs=[(2,"痛"),(0,"（"),(5,"）"),(3,"！"),(4,"っ"),(1,"・")]
for slot,ch in pairs:
    cm=cache[slot][1]
    if sum(sum(1 for v in r if v) for r in cm)<6: continue
    s=src(idx(int.from_bytes(ch.encode("cp932"),"big")))
    best=None
    for dy in range(-2,3):
        for dx in range(-2,3):
            same=0; tot=0
            for y in range(14):
                for x in range(28):
                    sy,sx=y+dy,x+dx
                    sv=s[sy][sx] if 0<=sy<16 and 0<=sx<32 else 0
                    same += (sv==cm[y][x]); tot+=1
            if best is None or same>best[0]: best=(same,tot,dy,dx)
    same,tot,dy,dx=best
    print("%s idx=%-5d 값 완전일치 %d/%d = %.1f%%  (dy=%d dx=%d)" %
          (ch,idx(int.from_bytes(ch.encode("cp932"),"big")),same,tot,100*same/tot,dy,dx))

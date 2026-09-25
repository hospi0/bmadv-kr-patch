import sys; sys.path.insert(0,".")
from find_glyph_tex import morton, decode
d=open(r"..\work\disc1\SYSTEM.DAT","rb").read()
sp=r"C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\0b7d618a-9996-40c4-89fe-7ab5b878aad1\scratchpad"
st=open(sp+r"\p1.bin","rb").read()
CHUNK=0x424E0; HDR=16; K=128; TEX=0x0080ABF0
def idx(c):
    if 0x8140<=c<=0x81BF: return (c+0x7EC0)&0xFFFF
    if 0x8240<=c<=0x83BF: return (c+0x7E40)&0xFFFF
    if 0x889F<=c<=0x9872: return (c+0x7961)&0xFFFF
    return c&0xFFFF
def src(i):
    o=CHUNK+HDR+i*K; g=d[o:o+K]
    return [[ (g[((x//16)*256+morton(x%16,y,4,False))>>2] >> (2*(((x//16)*256+morton(x%16,y,4,False))&3)))&3
              for x in range(32)] for y in range(16)]
px=decode(st,TEX,64,64,False)
def cell(slot):
    cx,cy=slot%2, slot//2
    return [[px[(cy*16+y)*64+cx*32+x] for x in range(32)] for y in range(16)]
for slot,ch in ((0,"（"),(1,"・"),(2,"痛"),(3,"！"),(4,"っ"),(5,"）")):
    cm=cell(slot); s=src(idx(int.from_bytes(ch.encode("cp932"),"big")))
    best=None
    for dy in range(-3,4):
        for dx in range(-3,4):
            e=0
            for y in range(16):
                for x in range(32):
                    sy,sx=y-dy,x-dx
                    sv=s[sy][sx] if 0<=sy<16 and 0<=sx<32 else 0
                    e += (sv==cm[y][x])
            if best is None or e>best[0]: best=(e,dy,dx)
    e,dy,dx=best
    print("%s  최고 %d/512 = %5.1f%%   dy=%+d dx=%+d" % (ch,e,100*e/512,dy,dx))

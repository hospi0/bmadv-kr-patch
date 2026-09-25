import sys; sys.path.insert(0,".")
from find_glyph_tex import morton, decode
d=open(r"..\work\disc1\SYSTEM.DAT","rb").read()
sp=r"C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\0b7d618a-9996-40c4-89fe-7ab5b878aad1\scratchpad"
st=open(sp+r"\p1.bin","rb").read()
CHUNK=0x424E0; HDR=16; K=128
TEX=0x0080ABF0
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
# 캐시 텍스처 전체(64x64) 를 풀고 32x16 셀 그대로 꺼낸다
px=decode(st,TEX,64,64,False)
def cache_cell(slot):
    cx,cy=slot%2, slot//2
    return [[px[(cy*16+y)*64 + cx*32 + x] for x in range(32)] for y in range(16)]
pairs=[(0,"（"),(1,"・"),(2,"痛"),(3,"！"),(4,"っ"),(5,"）")]
for slot,ch in pairs:
    cm=cache_cell(slot)
    s=src(idx(int.from_bytes(ch.encode("cp932"),"big")))
    exact=sum(1 for y in range(16) for x in range(32) if s[y][x]==cm[y][x])
    print("%s slot%d  32x16 값 완전일치 %d/512 = %.1f%%" % (ch,slot,exact,100*exact/512))
    if exact<512:
        bad=[(x,y,s[y][x],cm[y][x]) for y in range(16) for x in range(32) if s[y][x]!=cm[y][x]]
        print("     불일치 %d개, 예:" % len(bad), bad[:8])

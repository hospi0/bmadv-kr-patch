import sys; sys.path.insert(0,r"C:\claude\utils\dreamcast\PyPVR"); sys.path.insert(0,".")
from pypvr import Pypvr
from find_glyph_tex import decode
d=open(r"..\work\disc1\SYSTEM.DAT","rb").read()
sp=r"C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\0b7d618a-9996-40c4-89fe-7ab5b878aad1\scratchpad"
st=open(sp+r"\p1.bin","rb").read()
CHUNK=0x424E0; HDR=16; K=128; TEX=0x0080ABF0
tw=Pypvr().twiddle(32,16)          # linear i -> twiddled position
print("twiddle 표 길이", len(tw), "최대", max(tw))
def idx(c):
    if 0x8140<=c<=0x81BF: return (c+0x7EC0)&0xFFFF
    if 0x8240<=c<=0x83BF: return (c+0x7E40)&0xFFFF
    if 0x889F<=c<=0x9872: return (c+0x7961)&0xFFFF
    return c&0xFFFF
def src(i):
    o=CHUNK+HDR+i*K; g=d[o:o+K]
    m=[[0]*32 for _ in range(16)]
    for lin in range(512):
        s=tw[lin]
        v=(g[s>>2]>>(2*(s&3)))&3
        m[lin//32][lin%32]=v
    return m
px=decode(st,TEX,64,64,False)
def cell(slot):
    cx,cy=slot%2, slot//2
    return [[px[(cy*16+y)*64+cx*32+x] for x in range(32)] for y in range(16)]
tot=0; n=0
for slot,ch in ((0,"（"),(1,"・"),(2,"痛"),(3,"！"),(4,"っ"),(5,"）")):
    cm=cell(slot); s=src(idx(int.from_bytes(ch.encode("cp932"),"big")))
    e=sum(1 for y in range(16) for x in range(32) if s[y][x]==cm[y][x])
    tot+=e; n+=512
    print("%s  %d/512 = %5.1f%%" % (ch,e,100*e/512))
print("합계 %d/%d = %.1f%%" % (tot,n,100*tot/n))
print()
print("--- 痛 (PyPVR 트위들) ---")
for r in src(3114): print("   |"+"".join(" .+#"[v] for v in r)+"|")

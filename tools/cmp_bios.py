import os,sys; sys.path.insert(0,'.')
from bios_font import glyph
from glyph_extract import glyphs
sp = r"C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\0b7d618a-9996-40c4-89fe-7ab5b878aad1\scratchpad"
rom=open(r"D:\hospi\RetroArch\system\dc\dc_boot.bin","rb").read()
st1=open(os.path.join(sp,"p1.bin"),"rb").read()
gs=glyphs(st1,0x0080ABF0,64,64)
pairs=[(0,"\uff08"),(1,"\u30fb"),(2,"\u75db"),(3,"\uff01"),(4,"\u3063"),(5,"\uff09")]
def sample(g,sx,sy,ox,oy):
    out=[]
    for y in range(14):
        row=[]
        for x in range(28):
            u=(x-ox)*sx; v=(y-oy)*sy
            iu=int(round(u)); v0=int(v); v1=int(v+sy); val=0
            if 0<=iu<24:
                for vv in range(max(0,v0),min(24,max(v1,v0+1))): val|=g[vv][iu]
            row.append(val)
        out.append(row)
    return out
tot_a=tot_n=0
for slot,ch in pairs:
    cm=[[1 if v else 0 for v in r] for r in gs[slot][1]]
    if sum(map(sum,cm))<6:
        print("slot%d %s : too little ink, skip"%(slot,ch)); continue
    g24,n,off=glyph(rom,int.from_bytes(ch.encode("cp932"),"big"))
    best=(-1,0,0,0,0)
    for sx in (24/28,24/26,0.9,0.9231,0.95,1.0):
        for sy in (24/14,1.7143,1.6,1.8):
            for ox in range(-3,5):
                for oy in range(-2,3):
                    s=sample(g24,sx,sy,ox,oy)
                    a=sum(1 for y in range(14) for x in range(28) if s[y][x]==cm[y][x])
                    if a>best[0]: best=(a,sx,sy,ox,oy)
    a=best[0]; tot_a+=a; tot_n+=392
    print("%s (BIOS idx %4d) best %3d/392 = %5.1f%%  sx=%.3f sy=%.3f ox=%d oy=%d  cache_ink=%d"
          % (ch,n,a,100*a/392,best[1],best[2],best[3],best[4],sum(map(sum,cm))))
print("TOTAL %d/%d = %.1f%%" % (tot_a,tot_n,100*tot_a/tot_n))

import os,sys; sys.path.insert(0,".")
from bios_font import glyph
from glyph_extract import glyphs
sp = r"C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\0b7d618a-9996-40c4-89fe-7ab5b878aad1\scratchpad"
rom=open(r"D:\hospi\RetroArch\system\dc\dc_boot.bin","rb").read()
st1=open(os.path.join(sp,"p1.bin"),"rb").read()
gs=glyphs(st1,0x0080ABF0,64,64)
def cover(g24,sx,sy,ox,oy):
    out=[]
    for y in range(14):
        y0=(y-oy)*sy; y1=y0+sy; row=[]
        for x in range(28):
            x0=(x-ox)*sx; x1=x0+sx; s=0.0; a=0.0
            for yy in range(24):
                ov=max(0.0,min(y1,yy+1)-max(y0,yy))
                if ov<=0: continue
                for xx in range(24):
                    oh=max(0.0,min(x1,xx+1)-max(x0,xx))
                    if oh<=0: continue
                    a+=oh*ov; s+=oh*ov*g24[yy][xx]
            row.append(s/a if a>0 else 0.0)
        out.append(row)
    return out
for slot,ch in ((2,"\u75db"),(0,"\uff08"),(4,"\u3063"),(3,"\uff01")):
    cm=[[1 if v else 0 for v in r] for r in gs[slot][1]]
    g24,n,_=glyph(rom,int.from_bytes(ch.encode("cp932"),"big"))
    best=None
    for sx in (0.857,0.9,0.9231,0.95,1.0):
        for sy in (1.6,1.7143,1.8):
            for ox in range(-3,4):
                for oy in range(-2,3):
                    cv=cover(g24,sx,sy,ox,oy)
                    bios=[[1 if cv[y][x]>=0.5 else 0 for x in range(28)] for y in range(14)]
                    nb=sum(map(sum,bios))
                    if nb<4: continue
                    inside=sum(1 for y in range(14) for x in range(28) if bios[y][x] and cm[y][x])
                    rec=inside/nb
                    if best is None or rec>best[0]: best=(rec,nb,sum(map(sum,cm)),sx,sy,ox,oy)
    rec,nb,nc,sx,sy,ox,oy=best
    print("%s : BIOS 잉크 %3d 중 %5.1f%% 가 캐시 잉크 안에 들어감 (캐시 잉크 %3d)  sx=%.3f sy=%.3f ox=%d oy=%d"
          % (ch,nb,100*rec,nc,sx,sy,ox,oy))

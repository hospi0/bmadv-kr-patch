import os,sys; sys.path.insert(0,".")
from bios_font import glyph
from glyph_extract import glyphs
sp = r"C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\0b7d618a-9996-40c4-89fe-7ab5b878aad1\scratchpad"
rom=open(r"D:\hospi\RetroArch\system\dc\dc_boot.bin","rb").read()
st1=open(os.path.join(sp,"p1.bin"),"rb").read()
gs=glyphs(st1,0x0080ABF0,64,64)
def cover(g24,W,H,sx,sy,ox,oy):
    out=[]
    for y in range(H):
        y0=(y-oy)*sy; y1=y0+sy
        row=[]
        for x in range(W):
            x0=(x-ox)*sx; x1=x0+sx
            s=0.0;a=0.0
            for yy in range(24):
                oyv=max(0.0,min(y1,yy+1)-max(y0,yy))
                if oyv<=0: continue
                for xx in range(24):
                    oxv=max(0.0,min(x1,xx+1)-max(x0,xx))
                    if oxv<=0: continue
                    a+=oxv*oyv; s+=oxv*oyv*g24[yy][xx]
            row.append(s/a if a>0 else 0.0)
        out.append(row)
    return out
for slot,ch in ((2,"\u75db"),(0,"\uff08"),(4,"\u3063")):
    cm=gs[slot][1]
    g24,n,_=glyph(rom,int.from_bytes(ch.encode("cp932"),"big"))
    best=None
    for sx in (0.857,0.9,0.9231,0.95,1.0):
        for sy in (1.6,1.7143,1.8):
            for ox in range(-3,4):
                for oy in range(-2,3):
                    cv=cover(g24,28,14,sx,sy,ox,oy)
                    # 상관: 캐시 v -> 기대 커버리지 순서 (0 < 3 < 2 < 1)
                    buckets={0:[],1:[],2:[],3:[]}
                    for y in range(14):
                        for x in range(28):
                            buckets[cm[y][x]].append(cv[y][x])
                    if not buckets[1]: continue
                    m={k:(sum(v)/len(v) if v else -1) for k,v in buckets.items()}
                    score = (m[1]-m[0])
                    if best is None or score>best[0]: best=(score,sx,sy,ox,oy,m,{k:len(v) for k,v in buckets.items()})
    s,sx,sy,ox,oy,m,cnt=best
    print("%s (BIOS idx %d) sx=%.4f sy=%.4f ox=%d oy=%d" % (ch,n,sx,sy,ox,oy))
    print("   캐시값별 BIOS 평균 커버리지:  v0=%.3f(n=%d)  v3=%.3f(n=%d)  v2=%.3f(n=%d)  v1=%.3f(n=%d)"
          % (m[0],cnt[0],m[3],cnt[3],m[2],cnt[2],m[1],cnt[1]))

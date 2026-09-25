import sys; sys.path.insert(0,".")
d=open(r"..\work\disc1\SYSTEM.DAT","rb").read()
B=0x49820; K=256
NAMES={0:"space",1:"comma",5:"nakaguro",9:"excl",41:"paren-open",42:"paren-close",
       160:"A",172:"M",226:"i-hira",3114:"itami"}
def show(i,mode):
    g=d[B+i*K:B+(i+1)*K]
    rows=[]
    if mode=="4bpp32x16":
        W,H=32,16
        for y in range(H):
            r=""
            for x in range(W):
                b=g[(y*W+x)>>1]
                v=(b>>4)&0xF if (y*W+x)&1 else b&0xF
                r+= "#" if v else "."
            rows.append(r)
    elif mode=="1bpp32x64":
        W,H=32,64
        for y in range(H):
            r=""
            for x in range(W):
                bit=y*W+x
                r+= "#" if (g[bit>>3]>>(7-(bit&7)))&1 else "."
            rows.append(r)
    elif mode=="2bpp32x32":
        W,H=32,32
        for y in range(H):
            r=""
            for x in range(W):
                p=y*W+x
                v=(g[p>>2]>>(2*(p&3)))&3
                r+= "#" if v else "."
            rows.append(r)
    return rows
for mode in ("4bpp32x16","2bpp32x32"):
    print("############", mode)
    for i in (41,42,3114):
        print("--- %d (%s) ---" % (i,NAMES.get(i,"")))
        for r in show(i,mode): print("   "+r)
        print()

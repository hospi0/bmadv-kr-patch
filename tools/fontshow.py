import sys; sys.path.insert(0,".")
d=open(r"..\work\disc1\SYSTEM.DAT","rb").read()
CHUNK=0x424E0; HDR=16; K=128
def idx(code):
    if 0x8140<=code<=0x81BF: return (code+0x7EC0)&0xFFFF
    if 0x8240<=code<=0x83BF: return (code+0x7E40)&0xFFFF
    if 0x889F<=code<=0x9872: return (code+0x7961)&0xFFFF
    return code&0xFFFF
def art(i):
    o=CHUNK+HDR+i*K
    g=d[o:o+K]
    out=[]
    for y in range(16):
        r=""
        for x in range(32):
            p=y*32+x
            v=(g[p>>2]>>(2*(p&3)))&3
            r += " .+#"[v]*1
        out.append(r)
    return out
for ch in "痛何体中（）！・っだ":
    c=int.from_bytes(ch.encode("cp932"),"big"); i=idx(c)
    print("=== %s  SJIS 0x%04X → index %d (파일 0x%06X) ===" % (ch,c,i,CHUNK+HDR+i*K))
    for r in art(i): print("   "+r)
    print()

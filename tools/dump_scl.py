import sys, struct; sys.path.insert(0,".")
from cmp2 import load
from scl import parse_scl, parse_pvx, walk_pac, decode_tcw
for fn in ("SYSTEM.DAT","GRAPHIC.DAT"):
    c=load(r"..\work\disc1\%s"%fn)
    print("########", fn, "entries", c.count)
    for i in range(c.count):
        d=c.entry(i)
        if d[:4]==b"PAC ":
            subs=walk_pac(d)
            print(" entry %2d PAC subs=%d" % (i,len(subs)))
            for j,(o,ln) in enumerate(subs):
                mg=d[o:o+4]
                if mg==b"SCL ":
                    s=parse_scl(d,o); t=s["tcw"]
                    print("    [%2d] SCL  off=0x%06X len=0x%-7X tcw=0x%08X %-9s %-8s pal=%d n=%d m=%d offs=%s"
                          % (j,o,ln,t["raw"],t["fmt"],"twid" if t["twiddled"] else "lin",t["pal"],s["n"],s["m"],
                             ["0x%X"%x for x in s["offs"][:4]]))
                elif mg==b"PVX ":
                    p=parse_pvx(d,o)
                    print("    [%2d] PVX  off=0x%06X len=0x%-7X n=%d m=%d k=%d" % (j,o,ln,p["n"],p["m"],p["k"]))
                else:
                    print("    [%2d] ?    off=0x%06X len=0x%-7X head=%s" % (j,o,ln," ".join("%02X"%b for b in d[o:o+8])))
        elif d[:4]==b"SCL ":
            s=parse_scl(d,0); t=s["tcw"]
            print(" entry %2d SCL  len=0x%-7X tcw=0x%08X %-9s %-8s pal=%d n=%d m=%d" % (i,len(d),t["raw"],t["fmt"],"twid" if t["twiddled"] else "lin",t["pal"],s["n"],s["m"]))
        else:
            print(" entry %2d ?    len=0x%-7X head=%s" % (i,len(d)," ".join("%02X"%b for b in d[:8])))

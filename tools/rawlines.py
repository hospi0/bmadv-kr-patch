import sys,struct; sys.path.insert(0,".")
import mfdfont as F
from swap16_scan import scan
d=open(r"..\work\disc1\SCENARIO.DAT","rb").read()
runs=scan(d,2)
si=[k for k,(o,n,s) in enumerate(runs) if "痛っ" in s][0]
ei=[k for k in range(si,len(runs)) if "思ってた" in runs[k][2]][0]
for k in range(si,ei+1):
    off,n,s=runs[k]
    codes=[struct.unpack_from("<H",d,off+2*j)[0] for j in range(n)]
    bad=[(j,c) for j,c in enumerate(codes) if not (0<len(bytes([c>>8,c&0xFF]).decode("cp932","ignore"))>0)]
    marks=""
    for j,c in enumerate(codes):
        try: ch=c.to_bytes(2,"big").decode("cp932")
        except Exception: ch=None
        if ch is None: marks += " [%d]=0x%04X(idx %s)" % (j,c,F.sjis_to_index(c))
    print("[%2d] %2d자 %s%s" % (k-si,n,s,marks))

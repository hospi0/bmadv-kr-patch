import sys,struct; sys.path.insert(0,".")
from cmp2 import load
from twiddle import detwiddle_4bpp
from PIL import Image
import collections, math
c=load(r"..\work\disc1\SYSTEM.DAT")
d=c.entry(3)
data=d[0x980:]
cnt=collections.Counter()
for b in data[:65536]: cnt[b>>4]+=1; cnt[b&15]+=1
N=sum(cnt.values())
print("니블 분포 상위:", cnt.most_common(6), " 엔트로피=%.2f" % (-sum(v/N*math.log2(v/N) for v in cnt.values())))
sp=r"C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\0b7d618a-9996-40c4-89fe-7ab5b878aad1\scratchpad"
for w,h in ((256,256),(512,512),(128,128)):
    need=w*h//2
    if len(data)<need: continue
    px=detwiddle_4bpp(data[:need],w,h)
    Image.frombytes("L",(w,h),bytes(v*17 for v in px)).save(sp+r"\sclt_%dx%d.png"%(w,h))
    print("twiddled saved",w,h)

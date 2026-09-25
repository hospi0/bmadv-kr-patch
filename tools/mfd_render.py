import sys,collections; sys.path.insert(0,".")
from PIL import Image
sp=r"C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\0b7d618a-9996-40c4-89fe-7ab5b878aad1\scratchpad"
d=open(r"..\work\disc1\SYSTEM.DAT","rb").read()
A=0x424E0
body=d[A+0x80:A+0x80+0x30000]
nib=collections.Counter()
for x in body[:100000]: nib[x>>4]+=1; nib[x&15]+=1
print("니블 분포:", nib.most_common(8))
def r4(buf,w,h,lo_first=True):
    px=bytearray()
    for b in buf[:w*h//2]:
        a1=b&0xF; a2=(b>>4)&0xF
        if lo_first: px.append(a1*17); px.append(a2*17)
        else: px.append(a2*17); px.append(a1*17)
    return Image.frombytes("L",(w,h),bytes(px[:w*h]))
for w,h in ((256,256),(512,256),(128,256),(32,512),(64,256)):
    if len(body)>=w*h//2:
        r4(body,w,h).save(sp+r"\mfd_%dx%d.png"%(w,h)); print("saved",w,h)

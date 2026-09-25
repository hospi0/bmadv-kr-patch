import sys; sys.path.insert(0,".")
from PIL import Image
sp=r"C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\0b7d618a-9996-40c4-89fe-7ab5b878aad1\scratchpad"
ram=open(sp+r"\ram_p1.bin","rb").read()
d=ram[0x22C800:0x265000]
def render1(buf,w,h,msb=True):
    px=bytearray()
    for b in buf[:w*h//8]:
        for k in range(8):
            bit=(b>>(7-k))&1 if msb else (b>>k)&1
            px.append(255 if bit else 0)
    return Image.frombytes("L",(w,h),bytes(px[:w*h]))
for w,h,tag in ((512,256,"512x256"),(256,512,"256x512"),(384,256,"384x256"),(128,256,"128x256")):
    if len(d)>=w*h//8:
        render1(d,w,h).save(sp+r"\f1_%s.png"%tag); print("saved",tag)

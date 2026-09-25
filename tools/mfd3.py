import sys; sys.path.insert(0,".")
from PIL import Image
sp=r"C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\0b7d618a-9996-40c4-89fe-7ab5b878aad1\scratchpad"
d=open(r"..\work\disc1\SYSTEM.DAT","rb").read()
A=0x424E0+0x2000
def r2(off,w,h,lsb=True):
    px=bytearray()
    for b in d[off:off+w*h//4]:
        for k in range(4):
            v=(b>>(2*k))&3 if lsb else (b>>(6-2*k))&3
            px.append(v*85)
    return Image.frombytes("L",(w,h),bytes(px[:w*h]))
panels=[]
for w in (24,28,32,48,56,64,112,128):
    h=160
    panels.append(("w%d"%w, r2(A,w,h).resize((w*3,h*3),Image.NEAREST)))
W=sum(p[1].width+8 for p in panels)+8; H=max(p[1].height for p in panels)+16
s=Image.new("L",(W,H),40); x=8
for lab,im in panels: s.paste(im,(x,8)); x+=im.width+8
s.save(sp+r"\mfd3.png"); s.save(r"C:\claude\project\bmadv-kr-patch\my files\mfd\mfd3.png")
print("saved mfd3.png", [p[0] for p in panels])

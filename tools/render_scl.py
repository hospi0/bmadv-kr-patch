import sys,struct; sys.path.insert(0,".")
from cmp2 import load
from PIL import Image
c=load(r"..\work\disc1\SYSTEM.DAT")
d=c.entry(3)
# 표 끝 찾기: 값이 (row*0x1000 + col*0x10) 격자 규칙을 벗어나는 지점
n=0; off=0x20
vals=[]
while off+4<=len(d):
    v=struct.unpack_from("<I",d,off)[0]
    r,cc=divmod(v,0x1000)
    if cc%0x10!=0 or cc//0x10>=16: break
    vals.append(v); off+=4; n+=1
    if n>4000: break
print("표 항목 %d개, 표 끝 0x%X, 최대값 0x%X" % (n,off,max(vals)))
data=d[off:]
print("픽셀 데이터 후보 %d B" % len(data))
def render(buf,w,h,scale=1):
    px=bytearray()
    for b in buf[:w*h//2]:
        px.append((b&0xF)*17); px.append(((b>>4)&0xF)*17)
    im=Image.frombytes("L",(w,h),bytes(px[:w*h]))
    return im if scale==1 else im.resize((w*scale,h*scale),Image.NEAREST)
for w,h,tag in ((512,256,"512x256"),(512,512,"512x512"),(256,256,"256x256")):
    if len(data)>=w*h//2:
        render(data,w,h).save(r"C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\0b7d618a-9996-40c4-89fe-7ab5b878aad1\scratchpad\scl_%s.png"%tag)
        print("saved",tag)

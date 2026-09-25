import sys,os; sys.path.insert(0,r"C:\claude\utils\dreamcast\PyPVR"); sys.path.insert(0,".")
from pypvr import Pypvr
from PIL import Image
d=open(r"..\work\disc1\SYSTEM.DAT","rb").read()
CHUNK=0x424E0; HDR=16; K=128
tw=Pypvr().twiddle(32,16)
NG=(0xD2500-CHUNK-HDR)//K
print("글리프 수:",NG)
LUT=[0,255,170,85]      # 인덱스 0~3 → 밝기 (1이 가장 진함)
def glyph(i):
    o=CHUNK+HDR+i*K; g=d[o:o+K]
    buf=bytearray(32*16)
    for lin in range(512):
        s=tw[lin]; v=(g[s>>2]>>(2*(s&3)))&3
        y=(lin//32)^1; x=(lin%32)^1
        buf[y*32+x]=LUT[v]
    return Image.frombytes("L",(32,16),bytes(buf))
def sheet(start,count,cols,scale,name):
    rows=(count+cols-1)//cols
    im=Image.new("L",(cols*32,rows*16),0)
    for k in range(count):
        i=start+k
        if i>=NG: break
        im.paste(glyph(i),((k%cols)*32,(k//cols)*16))
    if scale!=1: im=im.resize((im.width*scale,im.height*scale),Image.NEAREST)
    im.save(name); print(name, im.size)
out=r"C:\claude\project\bmadv-kr-patch\my files\mfd"
sheet(0,NG,64,1,os.path.join(out,"font_all.png"))
sheet(0,400,20,3,os.path.join(out,"font_head.png"))
sheet(3000,400,20,3,os.path.join(out,"font_kanji.png"))

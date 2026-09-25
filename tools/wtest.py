import sys,shutil,os; sys.path.insert(0,".")
import mfdfont as F
from hangul_raster import Rasterizer, art
sp=r"C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\0b7d618a-9996-40c4-89fe-7ab5b878aad1\scratchpad"
src=r"..\work\disc1\SYSTEM.DAT"; dst=os.path.join(sp,"SYSTEM_test.DAT")
shutil.copyfile(src,dst)
data=bytearray(open(dst,"rb").read())
r=Rasterizer()
plan=[("亜",'안'),("唖",'녕'),("娃",'하')]
for jp,kr in plan:
    code=int.from_bytes(jp.encode("cp932"),"big")
    i=F.sjis_to_index(code)
    print("%s SJIS %04X → index %s" % (jp,code,i))
    if i is None: continue
    g=r.glyph(kr)
    F.write_glyph(data,i,g)
open(dst,"wb").write(data)
chk=open(dst,"rb").read()
allok=True
for jp,kr in plan:
    i=F.sjis_to_index(int.from_bytes(jp.encode("cp932"),"big"))
    same = F.read_glyph(chk,i)==r.glyph(kr)
    allok &= same
    print("  되읽기 %s → %s" % (kr,"일치" if same else "★불일치"))
print("전체 되읽기:", "통과" if allok else "실패")
print("크기 불변:", os.path.getsize(src)==os.path.getsize(dst), os.path.getsize(dst))
n=sum(1 for a,b in zip(open(src,"rb").read(),chk) if a!=b)
print("바뀐 바이트 수:", n, "(글리프 3개 × 128B =", 3*128, "이내여야 정상)")
print("\n--- 되읽은 '안' ---"); print(art(F.read_glyph(chk,F.sjis_to_index(int.from_bytes("亜".encode("cp932"),"big")))))

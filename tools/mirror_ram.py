import sys; sys.path.insert(0,".")
from font_mirror import scan
sp=r"C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\0b7d618a-9996-40c4-89fe-7ab5b878aad1\scratchpad"
data=open(sp+r"\ram_p1.bin","rb").read()
# 그럴듯한 (K,H) 조합만
combos=[(144,24),(98,14),(128,16),(72,12),(196,28),(256,32),(96,16),(192,24),
        (72,24),(64,16),(128,32),(48,16),(288,24),(256,16),(112,14),(160,20),(200,20)]
out=[]
for K,H in combos:
    r=scan(data,K,H,min_rows_frac=1.0)
    if r: print("K=%d H=%d → %d" % (K,H,len(r)))
    out+=r
print("RAM 완전일치 후보 %d" % len(out))
out.sort(key=lambda r:-r[6])
for B,K,H,mt,tot,p41,p3114 in out[:25]:
    print("   K=%-4d H=%-3d B=0x%08X (RAM 0x%08X)  행등식 %d/%d  ink(（)=%-4d ink(痛)=%-5d"
          % (K,H,B,0x8C000000+B,mt,tot,p41,p3114))

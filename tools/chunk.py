import sys,collections,math; sys.path.insert(0,".")
sp=r"C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\0b7d618a-9996-40c4-89fe-7ab5b878aad1\scratchpad"
d=open(r"..\work\disc1\SYSTEM.DAT","rb").read()
ram=open(sp+r"\ram_p1.bin","rb").read()
A=0x424E0; R=0x75F800
n=0
while A+n<len(d) and R+n<len(ram) and d[A+n]==ram[R+n]: n+=1
print("SYSTEM.DAT 0x%X ↔ RAM 0x8C%06X 연속 일치 = %d B (0x%X)" % (A,R,n,n))
print("→ 적재 구간 SYSTEM.DAT 0x%X ~ 0x%X" % (A,A+n))
print()
print("8KB 단위 성질:")
for k in range(0,n,0x2000):
    b=d[A+k:A+k+0x2000]
    nib=collections.Counter()
    for x in b: nib[x>>4]+=1; nib[x&15]+=1
    N=sum(nib.values())
    ent=-sum(v/N*math.log2(v/N) for v in nib.values() if v)
    used=sorted(i for i in range(16) if nib[i]>N*0.002)
    print("  +0x%06X  0비율=%.3f 엔트로피=%.2f 니블=%s %s" %
          (k,b.count(0)/len(b),ent,used," ".join("%02X"%x for x in b[:6])))

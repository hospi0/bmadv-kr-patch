import sys,struct,collections,math; sys.path.insert(0,".")
sp=r"C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\0b7d618a-9996-40c4-89fe-7ab5b878aad1\scratchpad"
ram=open(sp+r"\ram_p1.bin","rb").read()
ram2=open(sp+r"\ram_p2.bin","rb").read()
a=0x75F800
print("=== 0x8C75F800 선두 ===")
for i in range(0,0x60,16):
    row=ram[a+i:a+i+16]
    print("  %08X  %s  |%s|" % (0x8C000000+a+i," ".join("%02X"%b for b in row),
          "".join(chr(b) if 32<=b<127 else "." for b in row)))
# 비영 범위
s=a
while s>0 and any(ram[s-2048:s]): s-=2048
e=a
while e<len(ram) and any(ram[e:e+2048]): e+=2048
print("\n비영 구간: 0x%08X ~ 0x%08X  (%d B)" % (0x8C000000+s,0x8C000000+e,e-s))
d=ram[s:e]
nib=collections.Counter()
for x in d[:200000]: nib[x>>4]+=1; nib[x&15]+=1
N=sum(nib.values())
print("니블 엔트로피=%.2f  0비율=%.3f  쓰는 니블=%s" %
      (-sum(v/N*math.log2(v/N) for v in nib.values()), d.count(0)/len(d),
       [i for i in range(16) if nib[i]>N*0.001]))
print("p1==p2 ?", d==ram2[s:e])

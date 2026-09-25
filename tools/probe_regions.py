import sys,collections,math; sys.path.insert(0,".")
ram=open(r"C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\0b7d618a-9996-40c4-89fe-7ab5b878aad1\scratchpad\ram_p1.bin","rb").read()
regions=[(0xD6B800,0xFFF800,"2640KB"),(0xC8A000,0xD47800,"758KB"),(0x22C800,0x265000,"226KB"),
         (0x324800,0x345000,"130KB"),(0x74D800,0x769800,"112KB"),(0x1C1000,0x1D3000,"72KB")]
for a,b,tag in regions:
    d=ram[a:b]
    nib=collections.Counter()
    for x in d[:200000]: nib[x>>4]+=1; nib[x&15]+=1
    N=sum(nib.values())
    ent=-sum(v/N*math.log2(v/N) for v in nib.values())
    used=[i for i in range(16) if nib[i]>N*0.0005]
    print("0x8C%06X (%s) len=%d  니블엔트로피=%.2f  주로쓰는니블=%s  0비율=%.3f"
          % (a,tag,len(d),ent,used,d.count(0)/len(d)))

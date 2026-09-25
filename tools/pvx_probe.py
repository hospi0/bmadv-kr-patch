import sys,struct; sys.path.insert(0,".")
sp=r"C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\0b7d618a-9996-40c4-89fe-7ab5b878aad1\scratchpad"
ram=open(sp+r"\ram_p1.bin","rb").read()
def dump(off,n,label):
    print("=== %s @0x%08X ===" % (label,0x8C000000+off))
    for i in range(0,n,16):
        row=ram[off+i:off+i+16]
        print("  %08X  %s  |%s|" % (0x8C000000+off+i," ".join("%02X"%b for b in row),
              "".join(chr(b) if 32<=b<127 else "." for b in row)))
for a in (0x1D8300,0x1E7700,0x1E7A00,0x1D8200):
    dump(a,0x40,"ram")
    print()
# 텍스트 모듈 전역들이 가리키는 값
for a in (0x1D8318,0x1D831C,0x1D8218,0x1E773C,0x1E7740,0x1E7750,0x1E7760,0x1E7A30):
    v=struct.unpack_from("<I",ram,a)[0]
    print("0x%08X → 0x%08X" % (0x8C000000+a,v))

import sys,struct; sys.path.insert(0,".")
from cmp2 import load
c=load(r"..\work\disc1\SYSTEM.DAT")
d=c.entry(3)
print("SCL entry3 len=0x%X" % len(d))
for i in range(0,0x100,16):
    print("  %04X  %s" % (i," ".join("%02X"%b for b in d[i:i+16])))
print()
vals=struct.unpack_from("<64I",d,0x20)
print("0x20 부터 u32 64개:", ["0x%X"%v for v in vals])

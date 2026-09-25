import sys,struct; sys.path.insert(0,".")
sp=r"C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\0b7d618a-9996-40c4-89fe-7ab5b878aad1\scratchpad"
d=open(r"..\work\disc1\SYSTEM.DAT","rb").read()
ram=open(sp+r"\ram_p1.bin","rb").read()
A=0x424E0
print("=== SYSTEM.DAT 0x%X ===" % A)
for i in range(0,0xC0,16):
    row=d[A+i:A+i+16]
    print("  %06X  %s  |%s|" % (A+i," ".join("%02X"%b for b in row),
          "".join(chr(b) if 32<=b<127 else "." for b in row)))
print()
print("u32 LE:", ["0x%X"%v for v in struct.unpack_from("<16I",d,A)])
# RAM 사본과 비교
R=0x75F800
n=0
for k in range(0x20000):
    if A+k>=len(d) or R+k>=len(ram): break
    if d[A+k]!=ram[R+k]: break
    n+=1
print("\nSYSTEM.DAT 0x%X 와 RAM 0x8C%06X 가 앞에서부터 %d B 일치" % (A,R,n))

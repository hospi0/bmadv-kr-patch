import struct
PIX={0:"ARGB1555",1:"RGB565",2:"ARGB4444",3:"YUV422",4:"BUMP",5:"4BPP_PAL",6:"8BPP_PAL"}
DAT={1:"TWIDDLED",2:"TWIDDLED_MM",3:"VQ",4:"VQ_MM",5:"PAL4_TW",6:"PAL4_TW_MM",7:"PAL8_TW",8:"PAL8_TW_MM",
     9:"RECTANGLE",0xB:"STRIDE",0xD:"TWID_RECT",0x10:"SMALLVQ",0x11:"SMALLVQ_MM",0x12:"TWID_ALIAS_MM"}
d=open(r"..\work\disc1\SYSTEM.DAT","rb").read()
hits=[]; i=d.find(b"PVRT")
while i>=0: hits.append(i); i=d.find(b"PVRT",i+1)
print("PVRT 헤더 %d개" % len(hits))
for k,o in enumerate(hits):
    size,=struct.unpack_from("<I",d,o+4)
    px,df=d[o+8],d[o+9]
    w,h=struct.unpack_from("<HH",d,o+12)
    print("  [%03d] 0x%08X  size=%-9d %-9s %-14s %dx%d" % (k,o,size,PIX.get(px,"?%d"%px),DAT.get(df,"?%d"%df),w,h))

import sys,struct; sys.path.insert(0,".")
d=open(r"..\work\disc1\SYSTEM.DAT","rb").read()
A=0x424E0
# 뒤쪽 매직 찾기
for mg in (b"MFD ",b"PAC ",b"SCL ",b"PVX ",b"CMP2"):
    i=d.find(mg,A+4)
    print("다음 %r : %s" % (mg, ("0x%X (+0x%X)"%(i,i-A)) if i>=0 else "없음"))
print()
# 데이터부 앞 512B
print("=== 0x%X (헤더+0x80) 부터 ===" % (A+0x80))
for i in range(0x80,0x80+0x180,16):
    row=d[A+i:A+i+16]
    print("  +%04X  %s" % (i," ".join("%02X"%b for b in row)))
print()
# 비영 시작
k=0x80
while k<0x20000 and not any(d[A+k:A+k+16]): k+=16
print("헤더 뒤 첫 비영 = +0x%X" % k)
# 0x80 단위로 비영 여부 요약
line=""
for k in range(0,0x2000,0x80):
    line += "#" if any(d[A+k:A+k+0x80]) else "."
print("0x80 단위 비영 지도(앞 0x2000):")
print("  "+line)

import sys,struct; sys.path.insert(0,".")
import mfdfont as F
# 1) 되읽기: 패치된 SCENARIO.DAT 를 배정표로 해독
cmap={}
for k,l in enumerate(open(r"..\work\trans\part1_charmap.tsv",encoding="utf-8")):
    if k==0: continue
    h,s,i=l.rstrip("\n").split("\t"); cmap[int(s,16)]=h
d=open(r"..\work\build\SCENARIO.DAT","rb").read()
rows=[l.rstrip("\n").split("\t") for l in open(r"..\work\trans\part1_ko.tsv",encoding="utf-8")][1:]
print("=== 되읽기 (첫 사본) ===")
okall=True
for r in rows:
    if len(r)<5: continue
    off=int(r[1],16); n=int(r[2]); ko=r[4]
    s=""
    for j in range(n):
        c=struct.unpack_from("<H",d,off+2*j)[0]
        if c in cmap: s+=cmap[c]
        else:
            try: s+=c.to_bytes(2,"big").decode("cp932")
            except Exception: s+="?"
    exp=ko+"\u3000"*(n-len(ko))
    ok = s==exp
    okall &= ok
    print("  [%2s] %s %s" % (r[0], "OK " if ok else "★NG", s))
print("되읽기 전체:", "통과" if okall else "실패")
print()
# 2) Track3 섹터 구조 확인
p=r"C:\claude\roms\dc\Black-Matrix Advanced (Japan)\Black-Matrix Advanced (Japan) (Disc 1)\Black-Matrix Advanced (Japan) (Disc 1) (Track 3).bin"
f=open(p,"rb")
f.seek(0); s0=f.read(2352)
print("섹터0 선두16B:", " ".join("%02X"%b for b in s0[:16]))
print("섹터0 꼬리(2064~2352):", " ".join("%02X"%b for b in s0[2064:2096]),"...")
tail=s0[2064:]
print("EDC/ECC 영역 %d B, 0 비율 %.3f" % (len(tail), tail.count(0)/len(tail)))
f.seek(100*2352); s=f.read(2352)
print("섹터100 EDC/ECC 0비율 %.3f" % (s[2064:].count(0)/288))

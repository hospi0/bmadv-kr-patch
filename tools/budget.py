import sys,collections; sys.path.insert(0,".")
from swap16_scan import scan
NG=4608
def idx(c):
    if 0x8140<=c<=0x81BF: return (c+0x7EC0)&0xFFFF
    if 0x8240<=c<=0x83BF: return (c+0x7E40)&0xFFFF
    if 0x889F<=c<=0x9872: return (c+0x7961)&0xFFFF
    return None
print("=== 주소 가능한 인덱스 구간 ===")
for lo,hi,name in ((0x8140,0x81BF,"기호"),(0x8240,0x83BF,"영숫자+히라가나+가타카나"),(0x889F,0x9872,"한자")):
    print("  SJIS %04X~%04X  %-24s → index %4d~%4d  (%d칸)" % (lo,hi,name,idx(lo),idx(hi),hi-lo+1))
print("  글리프 총수 %d, 주소 가능 최대 index %d, 여유 %d" % (NG,idx(0x9872),NG-1-idx(0x9872)))
print()
print("=== 스크립트가 실제로 쓰는 문자 ===")
d=open(r"..\work\disc1\SCENARIO.DAT","rb").read()
runs=scan(d,2)
cnt=collections.Counter()
for off,n,s in runs:
    for ch in s: cnt[ch]+=1
tot=sum(cnt.values())
print("  총 %d자, 고유 %d자" % (tot,len(cnt)))
import unicodedata
def klass(ch):
    c=int.from_bytes(ch.encode("cp932","ignore") or b"\0\0","big") if len(ch.encode("cp932","ignore"))==2 else 0
    if 0x8140<=c<=0x81BF: return "기호"
    if 0x824F<=c<=0x829A: return "영숫자"
    if 0x829F<=c<=0x82F1: return "히라가나"
    if 0x8340<=c<=0x8396: return "가타카나"
    if 0x889F<=c<=0x9872: return "한자"
    return "기타"
g=collections.Counter()
u=collections.defaultdict(set)
for ch,n in cnt.items():
    k=klass(ch); g[k]+=n; u[k].add(ch)
for k in ("기호","영숫자","히라가나","가타카나","한자","기타"):
    if g[k] or u[k]: print("  %-8s 출현 %7d   고유 %4d" % (k,g[k],len(u[k])))

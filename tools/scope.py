import sys; sys.path.insert(0,".")
from swap16_scan import scan
d=open(r"..\work\disc1\SCENARIO.DAT","rb").read()
runs=scan(d,2)
# 시작·끝 찾기
si=ei=None
for k,(off,n,s) in enumerate(runs):
    if si is None and "痛っ" in s: si=k
    if "思ってた" in s: ei=k
print("시작 런 %d (0x%X), 끝 런 %d (0x%X)" % (si,runs[si][0],ei,runs[ei][0]))
print("범위 런 수 %d, 바이트 0x%X ~ 0x%X" % (ei-si+1, runs[si][0], runs[ei][0]+runs[ei][1]*2))
print()
tot=0
for k in range(si,ei+1):
    off,n,s=runs[k]
    tot+=n
    print("  [%3d] 0x%06X %3d자  %s" % (k-si,off,n,s))
print("\n총 %d자" % tot)

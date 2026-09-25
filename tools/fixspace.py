import io,sys
p=r"..\work\trans\part1_ko.tsv"
lines=open(p,encoding="utf-8").read().split("\n")
out=[]
for k,l in enumerate(lines):
    if k==0 or not l.strip(): out.append(l); continue
    f=l.split("\t")
    if len(f)>=5:
        f[4]=f[4].replace(" ","\u3000")
    out.append("\t".join(f))
open(p,"w",encoding="utf-8",newline="").write("\n".join(out))
print("ASCII 공백 → 전각 공백 치환 완료")

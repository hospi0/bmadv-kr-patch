import io
p=r"..\work\trans\part1_ko.tsv"
fix={
 "10":"（그…그건\u3000그렇고…",
 "13":"\u3000…내\u3000몸은…）",
 "15":"\u3000인데…어라！？）",
 "17":"\u3000……？？）",
}
lines=open(p,encoding="utf-8").read().split("\n")
out=[]
for k,l in enumerate(lines):
    f=l.split("\t")
    if k>0 and len(f)>=5 and f[0] in fix:
        old=f[4]; f[4]=fix[f[0]]
        print("[%s] %s → %s  (%d자, 한도 %s)" % (f[0],old,f[4],len(f[4]),f[2]))
        l="\t".join(f)
    out.append(l)
open(p,"w",encoding="utf-8",newline="").write("\n".join(out))
print("\n남은 ・ 확인:")
for l in open(p,encoding="utf-8").read().split("\n")[1:]:
    f=l.split("\t")
    if len(f)>=5 and "・" in f[4]: print("  [%s] %s" % (f[0],f[4]))

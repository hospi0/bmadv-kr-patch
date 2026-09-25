import collections
for name in ("PARAMETA","GRAPHIC","SYSTEM"):
    rows=[l.rstrip("\n").split("\t") for l in open(r"..\work\trans\%s_runs.tsv"%name,encoding="utf-8")][1:]
    rows=[r for r in rows if len(r)>=5]
    print("===== %s : %d행 =====" % (name,len(rows)))
    # 가나 비율로 «진짜 일본어»인지 본다 (노이즈는 한자·기호만 잔뜩)
    def kana_ratio(s):
        k=sum(1 for c in s if "\u3040"<=c<="\u30ff")
        return k/max(1,len(s))
    hi=[r for r in rows if kana_ratio(r[4])>=0.3]
    print("  가나 비율 30%% 이상인 행: %d (%.1f%%)" % (len(hi),100*len(hi)/len(rows)))
    print("  --- 가나 많은 표본 ---")
    for r in hi[:8]: print("     [%s] %s자 x%s  %s" % (r[0],r[1],r[2],r[4][:40]))
    lo=[r for r in rows if kana_ratio(r[4])<0.1]
    print("  --- 가나 거의 없는 표본(노이즈 의심) %d행 ---" % len(lo))
    for r in lo[:8]: print("     [%s] %s자 x%s  %s" % (r[0],r[1],r[2],r[4][:40]))
    print()

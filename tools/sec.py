p=r"F:\hospi\roms\dc roms\Black-Matrix Advanced (Japan)\Black-Matrix Advanced (Japan) (Disc 1)\Black-Matrix Advanced (Japan) (Disc 1) (Track 3).bin"
f=open(p,"rb")
for sec in (0,16,20,100,1000):
    f.seek(sec*2352); s=f.read(2352)
    print("섹터 %5d  sync=%s  head=%s  mode=%02X" % (sec," ".join("%02X"%b for b in s[:4])," ".join("%02X"%b for b in s[12:15]),s[15]))
    tail=s[2064:]
    print("           EDC/ECC 288B  0비율=%.3f  선두8=%s" % (tail.count(0)/288," ".join("%02X"%b for b in tail[:8])))

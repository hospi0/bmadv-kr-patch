# -*- coding: utf-8 -*-
r"""SFD 동영상 꺼내기·변환(2026-10-31) — 원본 GD 트랙 3(D: 읽기만)에서 *.SFD → work/movie/disc<n>/ · ffmpeg 로 my files/movie/disc<n>/*.mp4(볼 용도)
  디스크 2 에 디스크 1 과 같은 이름·같은 내용(md5)이 있으면 변환 건너뜀
  python tools/sfd_dump.py"""
import hashlib, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import gdi_iso

SRC = r'D:\hospi\My Documents\한글패치\DC\dc'
DISC = {1: os.path.join(SRC, 'Black-Matrix Advanced (Japan) (Disc 1)', 'Black-Matrix Advanced (Japan) (Disc 1) (Track 3).bin'),
        2: os.path.join(SRC, 'Black-Matrix Advanced (Japan) (Disc 2)', 'Black-Matrix Advanced (Japan) (Disc 2)', 'Black-Matrix Advanced (Japan) (Disc 2) (Track 3).bin')}
FF = r'C:\claude\utils\ffmpeg-9.0.1-essentials_build\bin\ffmpeg.exe'


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    seen = {}
    for n, p in DISC.items():
        tr, pvd, rl, rlen = gdi_iso.open_iso(p)
        ents = [e for e in gdi_iso.parse_dir(tr, rl, rlen) if e[0].upper().endswith('.SFD')]
        wd = os.path.join(ROOT, 'work', 'movie', 'disc%d' % n); md = os.path.join(ROOT, 'my files', 'movie', 'disc%d' % n)
        os.makedirs(wd, exist_ok=True); os.makedirs(md, exist_ok=True)
        for name, lba, ln, _ in ents:
            d = tr.read_bytes(lba, ln); h = hashlib.md5(d).hexdigest(); nm = name.strip('/')
            open(os.path.join(wd, nm), 'wb').write(d)
            if seen.get(nm) == h: print('disc%d %s = disc1 같음, 변환 생략' % (n, nm)); continue
            seen[nm] = h
            out = os.path.join(md, nm[:-4] + '.mp4')
            r = subprocess.run([FF, '-v', 'error', '-y', '-i', os.path.join(wd, nm), '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', out], capture_output=True, text=True)
            print('disc%d %-14s %9d B → %s %s' % (n, nm, ln, os.path.basename(out), 'OK' if r.returncode == 0 else '실패 ' + r.stderr[-200:]), flush=True)


if __name__ == '__main__':
    main()

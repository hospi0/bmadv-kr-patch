# -*- coding: utf-8 -*-
r"""동영상 음성 받아쓰기(2026-10-31, 아스카 work/movie/asr_op.py 를 넓힘) — work/movie/disc<n>/*.SFD(STAFF 제외 — 스태프 롤은 허락 받고)
  ffmpeg 16 kHz 모노 → 위스퍼 large-v3(VAD 끔, 앞 문맥 끔) → work/movie/asr/<디스크>_<이름>.tsv(시작·끝·문장) + 요약
  실행: C:\claude\utils\whisper-venv\Scripts\python.exe tools/movie_asr.py"""
import glob, os, subprocess, sys, wave
import numpy as np
from faster_whisper import WhisperModel
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FF = r'C:\claude\utils\ffmpeg-9.0.1-essentials_build\bin\ffmpeg.exe'
SKIP = ('STAFF.SFD',)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    m = WhisperModel('large-v3', device='cuda', compute_type='float16')
    od = os.path.join(ROOT, 'work', 'movie', 'asr'); os.makedirs(od, exist_ok=True)
    seen = set()
    for f in sorted(glob.glob(os.path.join(ROOT, 'work', 'movie', 'disc*', '*.SFD'))):
        nm = os.path.basename(f); disc = os.path.basename(os.path.dirname(f))
        if nm in SKIP or nm in seen: continue
        seen.add(nm)
        wav = os.path.join(od, '%s_%s.wav' % (disc, nm[:-4]))
        subprocess.run([FF, '-v', 'error', '-y', '-i', f, '-ac', '1', '-ar', '16000', wav], check=True)
        w = wave.open(wav); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; w.close()
        segs, info = m.transcribe(a, language='ja', beam_size=5, condition_on_previous_text=False, vad_filter=False)
        rows = ['%.2f\t%.2f\t%s' % (s.start, s.end, s.text.strip()) for s in segs]
        open(os.path.join(od, '%s_%s.tsv' % (disc, nm[:-4])), 'w', encoding='utf-8').write('\n'.join(rows) + '\n')
        print('%s %-12s %5.1f초 %d줄 | %s' % (disc, nm, len(a) / 16000, len(rows), ' / '.join(r.split('\t')[2] for r in rows)[:150]), flush=True)


if __name__ == '__main__':
    main()

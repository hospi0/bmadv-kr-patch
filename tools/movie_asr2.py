# -*- coding: utf-8 -*-
r"""받아쓰기 재시도(2026-10-31) — 첫 받아쓰기가 비거나 환각(ご視聴ありがとう·같은 말 되풀이)인 동영상: VAD 음성 구간마다 앞뒤 0.3초 붙여 잘라 따로 받아씀
  → work/movie/asr/<이름>.retry.tsv · 실행: C:\claude\utils\whisper-venv\Scripts\python.exe tools/movie_asr2.py 이름…"""
import os, sys, wave
import numpy as np
from faster_whisper import WhisperModel
from faster_whisper.vad import get_speech_timestamps, VadOptions
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    m = WhisperModel('large-v3', device='cuda', compute_type='float16')
    for nm in sys.argv[1:]:
        p = os.path.join(ROOT, 'work', 'movie', 'asr', nm + '.wav')
        f = wave.open(p); a = np.frombuffer(f.readframes(f.getnframes()), np.int16).astype(np.float32) / 32768
        ts = get_speech_timestamps(a, VadOptions(threshold=0.3, min_speech_duration_ms=150, min_silence_duration_ms=400))
        rows = []
        for t in ts:
            s0 = max(0, t['start'] - 4800); s1 = min(len(a), t['end'] + 4800)
            segs, _ = m.transcribe(a[s0:s1], language='ja', beam_size=5, condition_on_previous_text=False, vad_filter=False, temperature=0)
            txt = ' '.join(s.text.strip() for s in segs)
            rows.append('%.2f\t%.2f\t%s' % (t['start'] / 16000, t['end'] / 16000, txt))
        open(os.path.join(ROOT, 'work', 'movie', 'asr', nm + '.retry.tsv'), 'w', encoding='utf-8').write('\n'.join(rows) + '\n')
        print('==', nm); print('\n'.join(rows), flush=True)


if __name__ == '__main__':
    main()

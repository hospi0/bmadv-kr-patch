# -*- coding: utf-8 -*-
r"""동영상 자막 시작 시각 맞추기(2026-10-31 하스피: 자막 시작이 너무 빠름)
  받아쓰기(VAD 끔) 구간은 앞 구간 끝에 붙어 있어 말소리보다 일찍 시작함 → silero VAD(faster_whisper, 문턱 0.2 — 0.4 는 속삭임 «私は» 놓침) 말소리 구간으로
  자막마다 시작을 «그 자막 구간 안 첫 말소리 시작»으로 늦춤(앞당기지는 않음, 0.25초 미만 차이는 그대로)
  python tools/movie_onset.py [동영상 …] [--write]  (기본 = 바뀔 것만 보여 줌, --write = my files/tsv/bm_movie_001.tsv 시작 칸 고침·백업 work/movie/bm_movie_001.bak.tsv)
  ⚠️whisper-venv 파이썬으로: C:/claude/utils/whisper-venv/Scripts/python.exe"""
import csv, os, shutil, sys, wave
import numpy as np
from faster_whisper.vad import get_speech_timestamps, VadOptions
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TSV = os.path.join(ROOT, 'my files', 'tsv', 'bm_movie_001.tsv')
ASR = os.path.join(ROOT, 'work', 'movie', 'asr')


def speech(mv):
    w = wave.open(os.path.join(ASR, mv.replace('/', '_') + '.wav'))
    sr = w.getframerate(); ch = w.getnchannels()
    a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    if ch > 1: a = a.reshape(-1, ch).mean(1)
    assert sr == 16000, sr
    ts = get_speech_timestamps(a, VadOptions(threshold=0.2, min_silence_duration_ms=150, speech_pad_ms=60))
    return [(t['start'] / sr, t['end'] / sr) for t in ts]


ONLY = [a for a in sys.argv[1:] if not a.startswith('--')]               # 동영상 지정(없으면 전부) — 하스피가 짚은 것만 고칠 때


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    rows = list(csv.DictReader(open(TSV, encoding='utf-8'), delimiter='\t', quoting=csv.QUOTE_NONE))
    sp = {}; n = 0
    for r in rows:
        if not (r['KO'] or '').strip(): continue
        mv = r['동영상']
        if ONLY and mv not in ONLY: continue
        if mv not in sp:
            try: sp[mv] = speech(mv)
            except FileNotFoundError: sp[mv] = None
        if not sp[mv]: continue
        a, b = float(r['시작']), float(r['끝'])
        on = [s for s, e in sp[mv] if e > a + 0.1 and s < b - 0.4 and e - s >= 0.4]   # 0.4초 미만 조각 = 잡음(MS0301 1.19 초 딸깍)
        if not on: continue
        s = max(a, on[0])
        if s - a >= 0.25:
            print('%s %s %.2f → %.2f  %s' % (r['번호'], mv, a, s, r['KO'][:20])); r['시작'] = '%.2f' % s; n += 1
    print('고칠 자막', n)
    if '--write' in sys.argv and n:
        bak = os.path.join(ROOT, 'work', 'movie', 'bm_movie_001.bak.tsv')
        if not os.path.exists(bak): shutil.copyfile(TSV, bak)
        with open(TSV, 'w', encoding='utf-8', newline='\n') as o:
            o.write('\t'.join(rows[0].keys()) + '\n')
            for r in rows: o.write('\t'.join(r[k] or '' for k in rows[0].keys()) + '\n')


if __name__ == '__main__':
    main()

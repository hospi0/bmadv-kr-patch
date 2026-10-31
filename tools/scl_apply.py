# -*- coding: utf-8 -*-
r"""SCL 한글 화면을 빌드본 EVENT.DAT·SYSTEM.DAT 에 넣기(2026-10-31) — tools/scl_draw.py 결과 work/scl_out/<키>.npy
  디스크마다 원본 파일(work/disc1·disc2)의 SCL 화면을 조립해 «작업 키의 원본 화면과 바이트 같은 것»을 모두 찾아 바꿈
    → 디스크 1·2 에 똑같이 들어 있는 화면(디스크 경고 등)은 양쪽 다 · 키 이름의 디스크와 상관없음
  입력 = work/build(디스크1)·build2(디스크2) 의 <파일>.v07 (처음 실행 때 지금 파일을 .v07 로 보관 = v0.7 빌드 결과) → 항상 그것에서 시작(다시 돌려도 같음)
  검산: 바뀐 바이트가 해당 SCL 블록(지도+텍스처) 밖이면 중단 · 다시 읽어 조립 = 새 화면
  python tools/scl_apply.py"""
import os, shutil, struct, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import scl_ko as K, scl_screen as S
from scl_jobs import JOBS

OUT = os.path.join(ROOT, 'work', 'scl_out')
BUILD = {'disc1': 'build', 'disc2': 'build2'}


def originals():
    """작업 키 → (원본 화면 바이트, 새 화면)"""
    cache = {}; out = {}
    for key in JOBS:
        disc, fn, first = key.split('_'); first = int(first)
        if (disc, fn) not in cache:
            d = open(os.path.join(ROOT, 'work', disc, fn + '.DAT'), 'rb').read(); cache[(disc, fn)] = (d, S.pvrt_index(d))
        d, pv = cache[(disc, fn)]
        p = max(b[0] for b in S.scl_blocks(d) if b[0] < pv[first])
        new = np.load(os.path.join(OUT, key + '.npy'))
        out[K.read(d, p, pv)['screen'].tobytes()] = (key, new)
    return out


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    want = originals(); used = set()
    for disc, bd in BUILD.items():
        for fn in ('EVENT.DAT', 'SYSTEM.DAT'):
            cur = os.path.join(ROOT, 'work', bd, fn); base = cur + '.v07'
            if not os.path.exists(base): shutil.copyfile(cur, base)
            orig = open(os.path.join(ROOT, 'work', disc, fn), 'rb').read(); pvo = S.pvrt_index(orig)
            d = bytearray(open(base, 'rb').read()); pvd = S.pvrt_index(bytes(d))
            assert len(d) == len(orig) and pvd == pvo, (disc, fn, '빌드본 구조가 원본과 다름')
            n = 0; moved = 0; spans = []
            for p, *_ in S.scl_blocks(orig):
                try: info0 = K.read(orig, p, pvo)
                except AssertionError: continue
                hit = want.get(info0['screen'].tobytes())
                if not hit: continue
                key, new = hit
                info = K.read(d, p, pvd)
                if not np.array_equal(info['screen'], info0['screen']): sys.exit('⛔ %s %s %X: v0.7 빌드본 화면이 원본과 다름(다른 도구가 손댐)' % (disc, fn, p))
                moved += K.write(d, info, new); n += 1; used.add(key)
                spans.append((p, p + 0x20 + 4 * len(info['map'])))
                spans += [(k, k + 16 + 2 * 256 * 256) for k in info['pvrt']]
                assert np.array_equal(K.read(d, p, pvd)['screen'], new), (key, '다시 읽은 화면이 다름')
            base_b = open(base, 'rb').read()
            diff = np.flatnonzero(np.frombuffer(bytes(d), np.uint8) != np.frombuffer(base_b, np.uint8))
            ok = np.zeros(len(diff), bool)
            for s, e in spans: ok |= (diff >= s) & (diff < e)
            if not ok.all(): sys.exit('⛔ %s %s SCL 블록 밖 변경 %d' % (disc, fn, (~ok).sum()))
            open(cur, 'wb').write(bytes(d))
            print('%s %-10s SCL 화면 %d 바꿈(새 조각 자리 %d) · 바뀐 바이트 %d' % (disc, fn, n, moved, len(diff)))
    miss = set(JOBS) - used
    if miss: sys.exit('⛔ 디스크에서 못 찾은 작업: %s' % ' '.join(sorted(miss)))
    print('작업 %d 모두 반영' % len(JOBS))


if __name__ == '__main__':
    main()

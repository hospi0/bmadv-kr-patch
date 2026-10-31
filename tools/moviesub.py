# -*- coding: utf-8 -*-
r"""SFD 동영상 자막 굽기(2026-10-31, 아스카 work/movie/op_subs.py 를 일반화) — my files/tsv/bm_movie_001.tsv(KO 빈칸 = 자막 없음)
  모든 동영상 = MPEG-1 320×240 · 첫 GOP 13장 + GOP 15장(B 2장, 열린 GOP) · 24fps(fr 2, 주기 3750) 또는 30fps(fr 5, 주기 3000)
  1) 원본 앞 GOP 0‥SPLICE-1(마지막 자막 끝이 든 GOP 다음까지, 마지막 GOP 는 안 건드림) 프레임 + drawtext → ffmpeg mpeg1video(-g 15 -bf 2, 양자화 고정 q)
     · 그림 종류·시간 참조 차례가 원본과 같아야 함 · 자리(원래 ES 바이트) 넘치면 q 를 올려 다시
  2) 그림마다 «원래 그 그림이 시작하던 패킷 첫 바이트»에 맞춰 0 을 채워 넣음(버퍼 넘침 방지) → ES 길이 그대로
  3) 영상 패킷 자리에 그대로 다시 나눔 · 앞부분 패킷 PTS/DTS 새로 = PTS (GOP 첫 그림 번호+시간 참조)×주기 · DTS (코딩 순서+1)×주기
     (원본에서 같은 규칙인지 먼저 검산) · 그림이 시작 안 하는 패킷의 타임스탬프는 채움 바이트로
  파일 크기·소리(ADX) 패킷 그대로.
  python tools/moviesub.py [동영상 …] → work/movie/kr/disc<n>/<이름>.SFD + my files/movie/kr/<이름>.mp4(볼 용도)"""
import bisect, csv, os, re, struct, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
exec(open(os.path.join(HERE, 'sfd.py'), encoding='utf-8').read().split("if __name__")[0])     # packets()
FF = r'C:\claude\utils\ffmpeg-9.0.1-essentials_build\bin\ffmpeg.exe'
FONT = r'C:\claude\utils\font\nanum-gothic\NanumGothicBold.ttf'
TSV = os.path.join(ROOT, 'my files', 'tsv', 'bm_movie_001.tsv')
SAME = {'disc2/MS1108': 'disc1/PROLOGUE'}                                   # 같은 소리·같은 그림 → 같은 자막
PUNCT = ',.!?…~:;'
FS, LINE = 15, 18
LATE_MAX = 8192                                                        # 새 그림 «끝»이 원래 그 그림 끝보다 늦어도 되는 한도(B) — GOP 마다 넘지 않는 가장 좋은 q(재생 끊김 방지)


def cues():
    out = {}
    for r in csv.DictReader(open(TSV, encoding='utf-8'), delimiter='\t'):
        ko = (r['KO'] or '').strip()
        if not ko: continue
        ko = re.sub('([%s]) +' % re.escape(PUNCT), r'\1', ko)                  # 문장부호 뒤 공백 지움(규칙)
        out.setdefault(r['동영상'], []).append((float(r['시작']), float(r['끝']), ko))
    for a, b in SAME.items():
        if b in out: out[a] = out[b]
    return out


def gops(es):
    out = []; k = 0
    while True:
        k = es.find(b'\x00\x00\x01\xb8', k)
        if k < 0: return out
        out.append(k); k += 4


def pictures(es):
    out = []; k = 0
    while True:
        k = es.find(b'\x00\x00\x01\x00', k)
        if k < 0: return out
        v = struct.unpack_from('>H', es, k + 4)[0]
        out.append((k, (v >> 3) & 7, v >> 6)); k += 4


def get_ts(b, o):
    return ((b[o] >> 1) & 7) << 30 | b[o + 1] << 22 | (b[o + 2] >> 1) << 15 | b[o + 3] << 7 | b[o + 4] >> 1


def put_ts(b, o, mark, v):
    b[o] = mark | ((v >> 29) & 0xE) | 1
    b[o + 1] = (v >> 22) & 0xFF; b[o + 2] = ((v >> 14) & 0xFE) | 1
    b[o + 3] = (v >> 7) & 0xFF; b[o + 4] = ((v << 1) & 0xFE) | 1


def gop_first(es, cut):
    """코딩 순서 j → 그 그림이 든 GOP 의 첫 표시 번호(= 앞 GOP 들 그림 수 합)"""
    pics = pictures(es[:cut]); gp = gops(es[:cut]); out = []; gi = 0; first = 0; cnt = 0
    for j, (k, t, r) in enumerate(pics):
        while gi < len(gp) and gp[gi] < k:
            first = j; gi += 1
        out.append(first)
    return pics, out


def ts_walk(b, P):
    """영상 패킷마다 (패킷 첫 ES 위치, 머리 위치 q, 종류 0x20/0x30/0)"""
    pos = 0; out = []
    for i, sid, st, p, en in P:
        if sid != 0xE0: continue
        q = st
        while b[q] == 0xFF: q += 1
        if b[q] & 0xC0 == 0x40: q += 2
        out.append((pos, q, b[q] & 0xF0, en - p)); pos += en - p
    return out


def check_rule(b, P, es, per):
    pics, gs = gop_first(es, len(es)); starts = [k for k, _, _ in pics]; bad = 0; n = 0
    for pos, q, kind, ln in ts_walk(b, P):
        if kind not in (0x20, 0x30): continue
        j = bisect.bisect_left(starts, pos)
        if j >= len(pics) or starts[j] >= pos + ln: continue
        _, t, r = pics[j]; n += 1
        if get_ts(b, q) != (gs[j] + r) * per: bad += 1
        if kind == 0x30 and get_ts(b, q + 5) != (j + 1) * per: bad += 1
    return n, bad


MAXW = 304                                                             # 화면 320 − 양옆 8px(테두리 2 포함) — 넘는 줄은 낱말 단위로 다시 나눔(2026-10-31 MS1104 양쪽 잘림)


def text_w(s):
    from PIL import ImageFont
    f = ImageFont.truetype(FONT, FS)
    return f.getlength(s) + 4                                             # borderw 2 양쪽


def wrap(t):
    """／ 줄마다 MAXW 넘으면 낱말 단위로 고르게 나눔(줄 수 최소, 길이 균형)"""
    out = []
    for l in t.split('／'):
        if text_w(l) <= MAXW: out.append(l); continue
        w = l.split(' ')
        for n in range(2, len(w) + 1):
            best = None
            def go(i, k, acc):
                nonlocal best
                if k == 1:
                    s = ' '.join(w[i:])
                    if text_w(s) <= MAXW:
                        c = acc + [s]; m = max(text_w(x) for x in c)
                        if best is None or m < best[0]: best = (m, c)
                    return
                for j in range(i + 1, len(w) - k + 2):
                    s = ' '.join(w[i:j])
                    if text_w(s) > MAXW: break
                    go(j, k - 1, acc + [s])
            go(0, n, [])
            if best: out += best[1]; break
        else: sys.exit('⛔ 한 낱말이 화면 폭 넘음 %r' % l)
    return '／'.join(out)


def esc(t):
    return t.replace('\\', '\\\\').replace("'", '\u2019').replace(':', '\\:').replace(',', '\\,').replace('%', '\\%')


def burn(mv, subs):
    src_p = os.path.join(ROOT, 'work', 'movie', mv + '.SFD')
    src = open(src_p, 'rb').read(); P = packets(src)
    es = b''.join(src[p:e] for _, s, _, p, e in P if s == 0xE0)
    k = es.find(b'\x00\x00\x01\xb3'); fr = es[k + 7] & 15
    fps, per = {2: (24, 3750), 5: (30, 3000)}[fr]
    n, bad = check_rule(src, P, es, per)
    assert bad == 0, ('원본 타임스탬프 규칙 다름', mv, n, bad)
    G = gops(es); pics_all = pictures(es)
    # GOP 마다 표시 첫 번호(앞 GOP 그림 수 합)
    cnt = [sum(1 for kk, _, _ in pics_all if kk < g) for g in G] + [len(pics_all)]
    last = max(e for _, e, _ in subs)
    SPLICE = next((i for i in range(1, len(G)) if cnt[i] - 2 >= int(last * fps) + 2), len(G) - 1)  # 앞 B 2장 = 이전 표시
    SPLICE = min(SPLICE, len(G) - 1)
    nfr = cnt[SPLICE] - 2
    if last * fps > nfr: subs = [(a, min(b, nfr / fps - 0.05), t) for a, b, t in subs]
    cut = G[SPLICE]
    pages = []                                                            # 폭 넘어 다시 나눈 줄이 2줄 넘으면 2줄씩 쪽 나눔(시간은 글자 수 비례)
    for a, b, t in subs:
        ls = wrap(t).split('／')
        if len(ls) <= 2 or len(ls) == len(t.split('／')): pages.append((a, b, '／'.join(ls))); continue
        pg = [ls[i:i + 2] for i in range(0, len(ls), 2)]
        tot = sum(len(''.join(x)) for x in pg); s = a
        for x in pg:
            e = b if x is pg[-1] else s + (b - a) * len(''.join(x)) / tot
            pages.append((s, e, '／'.join(x))); s = e
    lines = []
    for a, b, t in pages:
        ls = t.split('／')
        for i, l in enumerate(ls):
            y = 'h-%d' % (14 + LINE * (len(ls) - i))
            lines.append("drawtext=fontfile='%s':text='%s':fontsize=%d:fontcolor=white:borderw=2:bordercolor=0x101010:"
                         "x=(w-text_w)/2:y=%s:enable='between(t,%.3f,%.3f)'" % (FONT.replace('\\', '/').replace(':', '\\:'), esc(l), FS, y, a, b))
    flt = os.path.join(ROOT, 'work', 'movie', 'kr', '_filter.txt'); os.makedirs(os.path.dirname(flt), exist_ok=True)
    open(flt, 'w', encoding='utf-8').write(',\n'.join(lines))
    head = os.path.join(ROOT, 'work', 'movie', 'kr', '_head.m1v')
    def units(e, lo, hi):
        gs = set(gops(e))
        return [kk - 8 if (kk - 8) in gs else kk for kk, _, _ in pictures(e) if lo <= kk < hi]
    vstarts = []; o = 0
    for _, sid, _, p, e in P:
        if sid == 0xE0: vstarts.append(o); o += e - p
    ou = units(es, G[0], cut); oe = ou[1:] + [cut]                       # 원래 그림 시작·끝(ES 위치)
    op = [(t, r) for _, t, r in pictures(es[:cut])]
    gidx = []                                                            # 그림 j 가 든 GOP 번호
    for kk, _, _ in pictures(es[:cut]): gidx.append(bisect.bisect_right(G, kk) - 1)
    enc = {}
    def chunks(q):
        """q 로 인코딩 → 그림마다 바이트 조각(GOP 머리는 앞 그림에 붙임 — units 와 같은 경계)"""
        if q not in enc:
            cmd = [FF, '-v', 'error', '-y', '-i', src_p, '-an', '-frames:v', str(nfr + 20), '-/filter:v', flt,
                   '-c:v', 'mpeg1video', '-g', '15', '-bf', '2', '-sc_threshold', '1000000000', '-q:v', str(q), '-f', 'mpeg1video', head]
            subprocess.run(cmd, check=True)
            he = open(head, 'rb').read(); HG = gops(he)
            npc = [(t, r) for kk, t, r in pictures(he) if kk < HG[SPLICE]]
            assert op == npc, ('그림 구조 다름', mv, q, len(op), len(npc))
            nu = units(he, HG[0], HG[SPLICE]) + [HG[SPLICE]]
            enc[q] = [he[nu[j]:nu[j + 1]] for j in range(len(ou))]
        return enc[q]
    QS = (2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 20, 24, 31)
    worst_c = chunks(QS[-1]); minrest = [0] * (len(ou) + 1)              # 그림 x 부터 끝까지 최저 화질 크기 합(뒤에 남길 자리)
    for x in range(len(ou) - 1, -1, -1): minrest[x] = minrest[x + 1] + len(worst_c[x])
    if G[0] + minrest[0] > cut: raise SystemExit('⛔ 최저 화질로도 자리 넘침 %s' % mv)
    buf = bytearray(es[:G[0]]); late = 0; used = []
    j = 0
    while j < len(ou):
        g = gidx[j]; js = [x for x in range(j, len(ou)) if gidx[x] == g]; nxt = js[-1] + 1
        for q in QS:
            c = chunks(q); tb = bytearray(); pos = len(buf); worst = 0
            for x in js:
                tgt = max(G[0], vstarts[bisect.bisect_right(vstarts, ou[x]) - 1])
                tgt = min(tgt, cut - minrest[x])                         # 뒤에 남길 자리 빼고(끝이 작은 GOP·검은 화면일 때)
                if pos + len(tb) < tgt: tb += bytes(tgt - pos - len(tb))
                tb += c[x]
                worst = max(worst, pos + len(tb) - oe[x])                # 새 그림 끝 − 원래 그림 끝
            if pos + len(tb) + minrest[nxt] <= cut and (worst <= LATE_MAX or q == QS[-1]): break
        else:
            raise SystemExit('⛔ GOP %d 자리 없음 %s' % (g, mv))
        buf += tb; late = max(late, worst); used.append(q); j = nxt
    if len(buf) > cut: raise SystemExit('⛔ 자리 넘침 %s %d > %d' % (mv, len(buf), cut))
    q = max(used); import collections; qd = dict(sorted(collections.Counter(used).items()))
    HG = [0] * (SPLICE + 1); HG[SPLICE] = len(buf)                        # 보고용(자리 %)
    new_es = bytes(buf) + bytes(cut - len(buf)) + es[cut:]
    assert len(new_es) == len(es)
    pics, gs = gop_first(new_es, cut); starts = [kk for kk, _, _ in pics]
    out = bytearray(src); fixed = stuffed = 0
    for (i, sid, st, p, en) in P:
        if sid != 0xE0: continue
    pos = 0
    for (i, sid, st, p, en) in P:
        if sid != 0xE0: continue
        ln = en - p
        out[p:en] = new_es[pos:pos + ln]
        if pos < cut:
            q0 = st
            while out[q0] == 0xFF: q0 += 1
            if out[q0] & 0xC0 == 0x40: q0 += 2
            kind = out[q0] & 0xF0
            if kind in (0x20, 0x30):
                j = bisect.bisect_left(starts, pos)
                if j < len(pics) and starts[j] < pos + ln:
                    _, t, r = pics[j]
                    if kind == 0x30:
                        put_ts(out, q0, 0x30, (gs[j] + r) * per); put_ts(out, q0 + 5, 0x10, (j + 1) * per)
                    else:
                        put_ts(out, q0, 0x20, (gs[j] + r) * per)
                    fixed += 1
                else:
                    nn = 5 if kind == 0x20 else 10
                    std = bytes(out[q0 - 2:q0]) if q0 - 2 >= st and out[q0 - 2] & 0xC0 == 0x40 else b''
                    hl = q0 + nn - st
                    out[st:q0 + nn] = b'\xff' * (hl - len(std) - 1) + std + b'\x0f'; stuffed += 1
        pos += ln
    assert len(out) == len(src)
    od = os.path.join(ROOT, 'work', 'movie', 'kr', os.path.dirname(mv)); os.makedirs(od, exist_ok=True)
    dst = os.path.join(ROOT, 'work', 'movie', 'kr', mv + '.SFD'); open(dst, 'wb').write(out)
    vd = os.path.join(ROOT, 'my files', 'movie', 'kr'); os.makedirs(vd, exist_ok=True)
    subprocess.run([FF, '-v', 'error', '-y', '-i', dst, '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
                    os.path.join(vd, mv.replace('/', '_') + '.mp4')], check=True)
    print('%-15s %dfps 자막 %2d · GOP %d/%d 교체 · GOP별 q %s · 자리 %d%% · 끝 늦음 %dB(한도 8KB) · 타임스탬프 %d 고침/%d 지움 · 원본 규칙 %d 일치'
          % (mv, fps, len(subs), SPLICE, len(G), qd, 100 * (HG[SPLICE] - HG[0]) // (cut - G[0]), late, fixed, stuffed, n), flush=True)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    C = cues(); want = sys.argv[1:] or sorted(C)
    for mv in want: burn(mv, C[mv])


if __name__ == '__main__':
    main()

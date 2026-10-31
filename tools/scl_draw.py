# -*- coding: utf-8 -*-
r"""SCL 화면 한글 그리기(2026-10-31) — 화면별 작업 = JOBS(tools/scl_jobs.py)
  표시 좌표 640×480(텍스처는 640×240 — 세로 2배로 보임)에서 «지우기 → 그리기» 후 세로 절반으로 줄여 RGB565 로
  바뀐 화소만 새 값(나머지 원래 u16 그대로) → work/scl_out/<디스크>_<파일>_<첫 텍스처>.npy · 미리보기 my files/그래픽미리보기/
  작업 항목:
    ('fill', (x0,y0,x1,y1), (r,g,b))                         — 상자를 한 색으로(검정 바탕 카드)
    ('h', 글, (x,y), 글꼴, 크기, 색, {opt})                  — 가로 글(opt: anchor='la'|'ma'|'ra', stroke=(폭,색), shadow=(dx,dy,색), glow=(반경,색))
    ('v', [열…오른쪽부터], (x오른쪽,y위), 글꼴, 크기, 색, {opt}) — 세로 글(열 간격 opt pitch, 줄 간격 opt lead) · … ― 등은 90° 돌림
  python tools/scl_draw.py [작업 이름 …]"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import scl_ko as K, scl_screen as S
from scl_jobs import JOBS

FONTS = {
    'blackhan': 'C:/claude/utils/font/logo/BlackHanSans.ttf',
    'myeongjo': r'C:\claude\utils\font\nanum-myeongjo\NanumMyeongjoExtraBold.ttf',
    'gothic': r'C:\claude\utils\font\nanum-gothic\NanumGothicExtraBold.ttf',
    'gothicb': r'C:\claude\utils\font\nanum-gothic\NanumGothicBold.ttf',
}
ROT = '…―ー～〜「」『』（）()[]－-~'
PREV = os.path.join(ROOT, 'my files', '그래픽미리보기')
OUT = os.path.join(ROOT, 'work', 'scl_out')
_cache = {}


_cmap = {}


def check_glyphs(name, text):
    """글꼴에 없는 글자는 조용히 빠짐(Black Han Sans 에 … 없음) — 그리기 전에 중단"""
    from fontTools.ttLib import TTFont
    path = FONTS.get(name, name)
    if path not in _cmap: _cmap[path] = set(TTFont(path).getBestCmap())
    miss = [c for c in text if c != ' ' and ord(c) not in _cmap[path]]
    if miss: raise SystemExit('⛔ 글꼴 %s 에 없는 글자 %r: %s' % (name, ''.join(miss), text))


def font(name, size):
    k = (name, size)
    if k not in _cache: _cache[k] = ImageFont.truetype(FONTS.get(name, name), size)
    return _cache[k]


def load(key):
    disc, fn, first = key.split('_'); first = int(first)
    d = open(os.path.join(ROOT, 'work', disc, fn + '.DAT'), 'rb').read(); pv = S.pvrt_index(d)
    p = max(b[0] for b in S.scl_blocks(d) if b[0] < pv[first])
    return d, K.read(d, p, pv)


def _layer(size):
    return Image.new('L', size, 0)


def _paint(img, mask, color, opt):
    """mask(L) 를 img(RGB) 에 효과와 함께 칠함"""
    if 'glow' in opt:
        r, c = opt['glow']; g = mask.filter(ImageFilter.MaxFilter(2 * r + 1)).filter(ImageFilter.GaussianBlur(r))
        img.paste(Image.new('RGB', img.size, c), (0, 0), g)
    if 'shadow' in opt:
        dx, dy, c = opt['shadow']; sh = Image.new('L', img.size, 0); sh.paste(mask, (dx, dy))
        img.paste(Image.new('RGB', img.size, c), (0, 0), sh)
    if 'stroke' in opt:
        w, c = opt['stroke']; st = mask.filter(ImageFilter.MaxFilter(2 * w + 1))
        img.paste(Image.new('RGB', img.size, c), (0, 0), st)
    img.paste(Image.new('RGB', img.size, color), (0, 0), mask)


def draw_h(img, text, xy, fname, size, color, opt):
    check_glyphs(fname, text)
    m = _layer(img.size); ImageDraw.Draw(m).text(xy, text, font=font(fname, size), fill=255, anchor=opt.get('anchor', 'la'))
    if 'italic' in opt:                                                  # 기울임(원문 주인 선택 글씨) — 기준선 y 에서 오른쪽으로 밀기
        s = opt['italic']; m = m.transform(m.size, Image.AFFINE, (1, s, -s * xy[1], 0, 1, 0), Image.BILINEAR)
    _paint(img, m, color, opt)


def fit_size(fname, size, text, ref):
    """text 의 잉크 높이가 ref(같은 size)의 잉크 높이와 같아지는 크기 — 숫자가 한글보다 낮게 그려지는 글꼴 보정"""
    h = lambda s, z: (lambda b: b[3] - b[1])(font(fname, z).getbbox(s))
    return max(1, round(size * h(ref, size) / max(1, h(text, size))))


def draw_v(img, cols, xy, fname, size, color, opt):
    check_glyphs(fname, ''.join(cols))
    f = font(fname, size); m = _layer(img.size)
    pitch = opt.get('pitch', int(size * 1.35)); lead = opt.get('lead', int(size * 1.08))
    x0, y0 = xy
    for ci, col in enumerate(cols):
        cx = x0 - ci * pitch - size // 2; y = y0
        for ch in col:
            if ch == ' ': y += lead // 2; continue
            g = Image.new('L', (size * 2, size * 2), 0); ImageDraw.Draw(g).text((size, size), ch, font=f, fill=255, anchor='mm')
            if ch in ROT: g = g.rotate(-90)
            if ch in '、。，．,.':                                         # 세로쓰기 쉼표·마침표 = 글자 칸 오른쪽 위
                g = Image.new('L', (size * 2, size * 2), 0); ImageDraw.Draw(g).text((size + size // 4, size - size // 3), ch, font=f, fill=255, anchor='lb')
            m.paste(g, (cx - size, y + size // 2 - size), g)
            y += lead
    _paint(img, m, color, opt)


def render(key, ops):
    d, info = load(key)
    rows, cols = info['screen'].shape
    disp = Image.fromarray(K.to_rgb(info['screen'])).resize((cols, rows * 2), Image.NEAREST)
    img = disp.copy()
    for op in ops:
        kind = op[0]
        if kind == 'bgimg':                                               # 복원한 바탕(텍스처 해상도 RGB .npy) 통째로 깔기
            bg = np.load(os.path.join(ROOT, op[1]))
            img = Image.fromarray(bg).resize((cols, rows * 2), Image.NEAREST)
        elif kind == 'fill':
            ImageDraw.Draw(img).rectangle(op[1], fill=op[2])
        elif kind == 'h':
            o = op[6] if len(op) > 6 else {}
            size = fit_size(op[3], op[4], op[1], o['match']) if 'match' in o else op[4]
            xy = op[2]
            if 'match' in o:                                              # 잉크 아랫선을 기준 글자에 맞춤(하스피: 숫자가 몇 도트 낮았음)
                an = o.get('anchor', 'la')
                rb = font(op[3], op[4]).getbbox(o['match'], anchor=an)[3]; tb = font(op[3], size).getbbox(op[1], anchor=an)[3]
                xy = (xy[0], xy[1] + rb - tb)
            draw_h(img, op[1], xy, op[3], size, op[5], {k: v for k, v in o.items() if k != 'match'})
        elif kind == 'erase':                                             # ('erase', 상자) — 상자 안 글자 화소(무채색 밝은 채움 + 어두운 테)만 판정해 주변으로 칠하기
            import cv2
            x0, y0, x1, y1 = op[1]; a = np.asarray(img).copy(); r = a[y0:y1, x0:x1].astype(int)
            mx = r.max(2); sat = mx - r.min(2)
            m = ((sat < 45) & ((mx > 165) | (mx < 75))).astype(np.uint8)
            m = cv2.dilate(m, np.ones((5, 5), np.uint8))
            full = np.zeros(a.shape[:2], np.uint8); full[y0:y1, x0:x1] = m
            img = Image.fromarray(cv2.inpaint(a, full, 5, cv2.INPAINT_TELEA))
        elif kind == 'xbg':                                               # ('xbg', 짝 화면 키, 상자) — 같은 바탕 짝 화면에서 글자 없는 화소를 가져와 지우기, 둘 다 글자면 주변 칠하기
            import cv2
            _, inf2 = load(op[1]); other = np.asarray(Image.fromarray(K.to_rgb(inf2['screen'])).resize((cols, rows * 2), Image.NEAREST)).copy()
            a = np.asarray(img).copy(); x0, y0, x1, y1 = op[2]
            def tm(arr):
                r = arr.astype(int); mx = r.max(2); sat = mx - r.min(2)
                m = ((sat < 50) & (mx > 150)).astype(np.uint8)                 # 흰·회색 글자
                m = cv2.dilate(m, np.ones((7, 7), np.uint8))                    # 그림자·테까지
                box = np.zeros(m.shape, np.uint8); box[y0:y1, x0:x1] = 1
                return (m & box) > 0
            ms, mo = tm(a), tm(other)
            take = ms & ~mo & np.any(a != other, 2)
            a[take] = other[take]
            rest = ms & ~take                                             # 글자로 판정된 화소는 무조건(두 화면 같은 자리 같은 글자 — ※ 줄 — 도)
            img = Image.fromarray(cv2.inpaint(a, rest.astype(np.uint8), 5, cv2.INPAINT_TELEA) if rest.any() else a)
        elif kind == 'erase_red':                                         # ('erase_red', 상자) — 빨간 글자(+밝은 테) 판정해 주변 칠하기(주인 선택)
            import cv2
            x0, y0, x1, y1 = op[1]; a = np.asarray(img).copy(); r = a[y0:y1, x0:x1].astype(int)
            m = (((r[..., 0] - r[..., 2]) > 40) | ((r[..., 0] > 200) & (r[..., 0] - r[..., 2] > 15))).astype(np.uint8)
            m = cv2.dilate(m, np.ones((7, 7), np.uint8))
            full = np.zeros(a.shape[:2], np.uint8); full[y0:y1, x0:x1] = m
            img = Image.fromarray(cv2.inpaint(a, full, 7, cv2.INPAINT_TELEA))
        elif kind == 'icon':                                              # 원본 그림 조각 옮기기 ('icon', 원본 상자, 놓을 왼쪽 위)
            img.paste(disp.crop(op[1]), op[2])
        elif kind == 'hseq':                                              # 한 줄 안에 색 다른 글·아이콘 차례로 ('hseq', [(글, 색)|('@', 원본 상자)], (x 왼쪽, y 가운데), 글꼴, 크기, {opt})
            x, yc = op[2]; f = font(op[3], op[4]); o = op[5] if len(op) > 5 else {}
            for it in op[1]:
                if it[0] == '@':
                    box = it[1]; ic = disp.crop(box); img.paste(ic, (int(x) + 2, int(yc - ic.height / 2))); x += ic.width + 4; continue
                s, col = it; check_glyphs(op[3], s)
                draw_h(img, s, (x, yc), op[3], op[4], col, dict(o, anchor='lm')); x += f.getlength(s)
        elif kind == 'v':
            draw_v(img, op[1], op[2], op[3], op[4], op[5], op[6] if len(op) > 6 else {})
    a = np.asarray(img).astype(np.uint16)
    half = ((a[0::2] + a[1::2]) // 2).astype(np.uint8)                   # 세로 2배 표시 → 텍스처 줄
    new16 = K.from_rgb(half)
    chg = np.any(np.asarray(img)[0::2] != np.asarray(disp)[0::2], 2) | np.any(np.asarray(img)[1::2] != np.asarray(disp)[1::2], 2)
    out = info['screen'].copy(); out[chg] = new16[chg]
    os.makedirs(OUT, exist_ok=True); np.save(os.path.join(OUT, key + '.npy'), out)
    # 미리보기: 원본 | 한글 (실제 텍스처 값을 다시 세로 2배로)
    os.makedirs(PREV, exist_ok=True)
    after = Image.fromarray(K.to_rgb(out)).resize((cols, rows * 2), Image.NEAREST)
    pv = Image.new('RGB', (cols * 2 + 16, rows * 2), (60, 60, 60)); pv.paste(disp, (0, 0)); pv.paste(after, (cols + 16, 0))
    try: pv.save(os.path.join(PREV, key + '.png'))
    except OSError: print('  (미리보기 %s 저장 막힘 — 보기 창에 열려 있음, 건너뜀)' % key)
    return int(chg.sum())


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    want = [a for a in sys.argv[1:] if not a.startswith('--')] or list(JOBS)
    for k in want:
        n = render(k, JOBS[k])
        print('%-22s 바뀐 화소 %d' % (k, n))


if __name__ == '__main__':
    main()

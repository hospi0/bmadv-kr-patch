# -*- coding: utf-8 -*-
"""sh4dis.py — 드림캐스트 SH-4 디스어셈블러.

GDM 프로젝트에 편입해 둔 sh2dis.py(TrekkiesUnite118 계보, MIT
`tools/third_party/new-parm-archives-tools`)의 디코드 표를 바탕으로 하되
**드림캐스트에 맞게 고친 것**:

  - 새턴 SH-2 는 빅엔디언, **드림캐스트 SH-4 는 리틀엔디언** → 명령어를 `<H` 로 읽는다.
  - `mov.l @(disp,PC)` / `mov.w @(disp,PC)` 의 **리터럴 값을 실제로 읽어 주석에 단다**
    (하드웨어 주소·테이블 포인터 추적이 목적이므로 이게 핵심이다).
  - 분기 지연 슬롯을 표시한다.

⚠️ 이 도구는 «읽기용»이다. 코드 생성·이동에는 쓰지 않는다
(그 경우 명령 집합 전체 검산이 필요 — project-conventions §2.3).
"""
import argparse
import struct

DELAYED = ("rts", "rte", "bra ", "bsr ", "braf", "bsrf", "jmp ", "jsr ", "bt/s", "bf/s")


def s8(v):
    return v - 256 if v >= 128 else v


def s12(v):
    return v - 4096 if v >= 2048 else v


def dis(op, pc):
    n = (op >> 8) & 0xF
    m = (op >> 4) & 0xF
    i8 = op & 0xFF
    d8 = op & 0xFF
    d4 = op & 0xF
    i12 = op & 0xFFF
    H = op >> 12
    if op == 0x000B: return "rts"
    if op == 0x0009: return "nop"
    if op == 0x001B: return "sleep"
    if op == 0x002B: return "rte"
    if op == 0x0008: return "clrt"
    if op == 0x0018: return "sett"
    if op == 0x0028: return "clrmac"
    if op == 0x0019: return "div0u"
    if op == 0x0038: return "ldtlb"
    if op == 0x0048: return "clrs"
    if op == 0x0058: return "sets"
    if H == 0x0:
        lo = op & 0xF
        if lo == 0xC: return "mov.b @(r0,r%d),r%d" % (m, n)
        if lo == 0xD: return "mov.w @(r0,r%d),r%d" % (m, n)
        if lo == 0xE: return "mov.l @(r0,r%d),r%d" % (m, n)
        if lo == 0x4: return "mov.b r%d,@(r0,r%d)" % (m, n)
        if lo == 0x5: return "mov.w r%d,@(r0,r%d)" % (m, n)
        if lo == 0x6: return "mov.l r%d,@(r0,r%d)" % (m, n)
        if lo == 0x7: return "mul.l r%d,r%d" % (m, n)
        b = op & 0xFF
        t = {0x29: "movt r%d", 0x2A: "sts pr,r%d", 0x0A: "sts mach,r%d",
             0x1A: "sts macl,r%d", 0x23: "braf r%d", 0x03: "bsrf r%d",
             0x02: "stc sr,r%d", 0x12: "stc gbr,r%d", 0x22: "stc vbr,r%d",
             0x32: "stc ssr,r%d", 0x5A: "sts fpul,r%d", 0x6A: "sts fpscr,r%d",
             0x83: "pref @r%d", 0x93: "ocbi @r%d", 0xA3: "ocbp @r%d", 0xB3: "ocbwb @r%d",
             0xC3: "movca.l r0,@r%d"}
        if b in t: return t[b] % n
    if H == 0x1: return "mov.l r%d,@(%d,r%d)" % (m, d4 * 4, n)
    if H == 0x2:
        t = {0: "mov.b r%d,@r%d", 1: "mov.w r%d,@r%d", 2: "mov.l r%d,@r%d",
             4: "mov.b r%d,@-r%d", 5: "mov.w r%d,@-r%d", 6: "mov.l r%d,@-r%d",
             7: "div0s r%d,r%d", 8: "tst r%d,r%d", 9: "and r%d,r%d", 10: "xor r%d,r%d",
             11: "or r%d,r%d", 12: "cmp/str r%d,r%d", 13: "xtrct r%d,r%d",
             14: "mulu.w r%d,r%d", 15: "muls.w r%d,r%d"}
        if d4 in t: return t[d4] % (m, n)
    if H == 0x3:
        t = {0: "cmp/eq r%d,r%d", 2: "cmp/hs r%d,r%d", 3: "cmp/ge r%d,r%d",
             4: "div1 r%d,r%d", 5: "dmulu.l r%d,r%d", 6: "cmp/hi r%d,r%d",
             7: "cmp/gt r%d,r%d", 8: "sub r%d,r%d", 10: "subc r%d,r%d",
             11: "subv r%d,r%d", 12: "add r%d,r%d", 13: "dmuls.l r%d,r%d",
             14: "addc r%d,r%d", 15: "addv r%d,r%d"}
        if d4 in t: return t[d4] % (m, n)
    if H == 0x4:
        lo = op & 0xFF
        u = {0x00: "shll r%d", 0x01: "shlr r%d", 0x04: "rotl r%d", 0x05: "rotr r%d",
             0x08: "shll2 r%d", 0x09: "shlr2 r%d", 0x18: "shll8 r%d", 0x19: "shlr8 r%d",
             0x28: "shll16 r%d", 0x29: "shlr16 r%d", 0x20: "shal r%d", 0x21: "shar r%d",
             0x24: "rotcl r%d", 0x25: "rotcr r%d", 0x10: "dt r%d", 0x11: "cmp/pz r%d",
             0x15: "cmp/pl r%d", 0x0B: "jsr @r%d", 0x2B: "jmp @r%d",
             0x0E: "ldc r%d,sr", 0x1E: "ldc r%d,gbr", 0x2E: "ldc r%d,vbr",
             0x0A: "lds r%d,mach", 0x1A: "lds r%d,macl", 0x2A: "lds r%d,pr",
             0x5A: "lds r%d,fpul", 0x6A: "lds r%d,fpscr",
             0x06: "lds.l @r%d+,mach", 0x16: "lds.l @r%d+,macl", 0x26: "lds.l @r%d+,pr",
             0x22: "sts.l pr,@-r%d", 0x02: "sts.l mach,@-r%d", 0x12: "sts.l macl,@-r%d",
             0x07: "ldc.l @r%d+,sr", 0x17: "ldc.l @r%d+,gbr",
             0x0F: "mac.w @r%d+", 0x1F: "mac.l @r%d+"}
        if lo in u: return u[lo] % n
        if (op & 0xF) == 0xC: return "shad r%d,r%d" % (m, n)
        if (op & 0xF) == 0xD: return "shld r%d,r%d" % (m, n)
    if H == 0x5: return "mov.l @(%d,r%d),r%d" % (d4 * 4, m, n)
    if H == 0x6:
        t = {0: "mov.b @r%d,r%d", 1: "mov.w @r%d,r%d", 2: "mov.l @r%d,r%d", 3: "mov r%d,r%d",
             4: "mov.b @r%d+,r%d", 5: "mov.w @r%d+,r%d", 6: "mov.l @r%d+,r%d", 7: "not r%d,r%d",
             8: "swap.b r%d,r%d", 9: "swap.w r%d,r%d", 10: "negc r%d,r%d", 11: "neg r%d,r%d",
             12: "extu.b r%d,r%d", 13: "extu.w r%d,r%d", 14: "exts.b r%d,r%d", 15: "exts.w r%d,r%d"}
        if d4 in t: return t[d4] % (m, n)
    if H == 0x7: return "add #%d,r%d" % (s8(i8), n)
    if H == 0x8:
        sub = (op >> 8) & 0xF
        if sub == 0: return "mov.b r0,@(%d,r%d)" % (d4, m)
        if sub == 1: return "mov.w r0,@(%d,r%d)" % (d4 * 2, m)
        if sub == 4: return "mov.b @(%d,r%d),r0" % (d4, m)
        if sub == 5: return "mov.w @(%d,r%d),r0" % (d4 * 2, m)
        if sub == 8: return "cmp/eq #%d,r0" % s8(i8)
        if sub == 9: return "bt %08x" % (pc + 4 + s8(i8) * 2)
        if sub == 0xB: return "bf %08x" % (pc + 4 + s8(i8) * 2)
        if sub == 0xD: return "bt/s %08x" % (pc + 4 + s8(i8) * 2)
        if sub == 0xF: return "bf/s %08x" % (pc + 4 + s8(i8) * 2)
    if H == 0x9: return ("mov.w @(%d,pc),r%d" % (d8 * 2, n), pc + 4 + d8 * 2, 2)
    if H == 0xA: return "bra %08x" % (pc + 4 + s12(i12) * 2)
    if H == 0xB: return "bsr %08x" % (pc + 4 + s12(i12) * 2)
    if H == 0xC:
        sub = (op >> 8) & 0xF
        t = {0: "mov.b r0,@(%d,gbr)" % d8, 1: "mov.w r0,@(%d,gbr)" % (d8 * 2),
             2: "mov.l r0,@(%d,gbr)" % (d8 * 4), 3: "trapa #%d" % i8,
             4: "mov.b @(%d,gbr),r0" % d8, 5: "mov.w @(%d,gbr),r0" % (d8 * 2),
             6: "mov.l @(%d,gbr),r0" % (d8 * 4),
             7: "mova @(%d,pc),r0" % (d8 * 4), 8: "tst #%d,r0" % i8,
             9: "and #%d,r0" % i8, 10: "xor #%d,r0" % i8, 11: "or #%d,r0" % i8,
             12: "tst.b #%d,@(r0,gbr)" % i8, 13: "and.b #%d,@(r0,gbr)" % i8,
             14: "xor.b #%d,@(r0,gbr)" % i8, 15: "or.b #%d,@(r0,gbr)" % i8}
        if sub in t: return t[sub]
    if H == 0xD: return ("mov.l @(%d,pc),r%d" % (d8 * 4, n), (pc & ~3) + 4 + d8 * 4, 4)
    if H == 0xE: return "mov #%d,r%d" % (s8(i8), n)
    if H == 0xF: return "(fpu) .word %04x" % op
    return ".word %04x" % op


def run(data, base, start, count, out=print):
    pc = start
    prev_delayed = False
    for _ in range(count):
        o = pc - base
        if o < 0 or o + 2 > len(data):
            break
        op = struct.unpack_from("<H", data, o)[0]
        r = dis(op, pc)
        note = ""
        if isinstance(r, tuple):
            text, lit_addr, size = r
            lo = lit_addr - base
            if 0 <= lo and lo + size <= len(data):
                val = struct.unpack_from("<I" if size == 4 else "<H", data, lo)[0]
                note = "  ; [%08x] = 0x%08x" % (lit_addr, val)
            r = text
        mark = "  _" if prev_delayed else ""
        out("%08x: %04x  %s%s%s" % (pc, op, r, note, mark))
        prev_delayed = any(r.startswith(p) for p in DELAYED)
        pc += 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--base", default="0x8C000000")
    ap.add_argument("--start", required=True)
    ap.add_argument("--count", type=int, default=200)
    a = ap.parse_args()
    run(open(a.file, "rb").read(), int(a.base, 0), int(a.start, 0), a.count)


if __name__ == "__main__":
    main()

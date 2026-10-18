"""Schematic readability check: text/text and text/wire overlaps per sheet.
Text boxes come from the plotted PDF (exact), wires from the .kicad_sch files. Usage: sch_check.py <dir>"""
import sys, glob, os
import pymupdf as f
from kiutils.schematic import Schematic

d = sys.argv[1]
pdf = f.open(f"{d}/sch.pdf")
S = 25.4 / 72
order = ["root", "llc", "pri_aux", "sbb", "sec_aux", "mcu", "sense", "can", "io"]
tot = [0, 0]
verbose = len(sys.argv) > 2
for i, name in enumerate(order):
    if i == 0:
        continue
    page = pdf[i]
    spans = []
    for b in page.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            for sp in l["spans"]:
                t = sp["text"].strip()
                if not t:
                    continue
                x0, y0, x1, y1 = [v * S for v in sp["bbox"]]
                h = y1 - y0
                spans.append((t, (x0 + 0.1, y0 + 0.25 * h, x1 - 0.1, y1 - 0.25 * h)))
    spans = [s for s in spans if s[1][1] < 255]          # ignore the title block
    seen, uniq = set(), []
    for t, bx in spans:
        k = (t, round(bx[0], 1), round(bx[1], 1))
        if k not in seen:
            seen.add(k); uniq.append((t, bx))
    spans = uniq
    sch = Schematic.from_file(f"{d}/{name}.kicad_sch")
    wires = []
    for w in sch.graphicalItems:
        p = w.points
        wires.append((p[0].X, p[0].Y, p[1].X, p[1].Y))
    labs = {}
    for l in list(sch.labels) + list(sch.globalLabels):
        labs.setdefault(l.text, []).append((l.position.X, l.position.Y))

    def own(t, w):
        x1, y1, x2, y2 = w
        for (px, py) in labs.get(t, []):
            if (x1 == x2 == px and min(y1, y2) - 1e-3 <= py <= max(y1, y2) + 1e-3) or (y1 == y2 == py and min(x1, x2) - 1e-3 <= px <= max(x1, x2) + 1e-3):
                return True
        return False
    tt, tw = [], []
    for a in range(len(spans)):
        for b in range(a + 1, len(spans)):
            A, B = spans[a][1], spans[b][1]
            dx = min(A[2], B[2]) - max(A[0], B[0]); dy = min(A[3], B[3]) - max(A[1], B[1])
            if spans[a][0].isdigit() and len(spans[a][0]) <= 2 or spans[b][0].isdigit() and len(spans[b][0]) <= 2:
                continue
            if dx > 0.15 and dy > 0.1:
                tt.append((spans[a][0], spans[b][0], round(A[0], 1), round(A[1], 1)))
    for t, A in spans:
        if len(t) <= 2 and t.isdigit():               # pin numbers sit on their pins by design
            continue
        for (x1, y1, x2, y2) in wires:
            if own(t, (x1, y1, x2, y2)):
                continue
            if x1 == x2 and A[0] < x1 < A[2] and min(y1, y2) < A[3] and max(y1, y2) > A[1]:
                tw.append((t, round(A[0], 1), round(A[1], 1))); break
            if y1 == y2 and A[1] < y1 < A[3] and min(x1, x2) < A[2] and max(x1, x2) > A[0]:
                tw.append((t, round(A[0], 1), round(A[1], 1))); break
    tot[0] += len(tt); tot[1] += len(tw)
    print(f"{name:8s} text/text {len(tt):3d}   text/wire {len(tw):3d}")
    if verbose:
        for x in tt: print("   TT", x)
        for x in tw: print("   TW", x)
print("TOTAL", tot)

"""Connector silkscreen: J1/J2 polarity, J3/J4 CAN pin names, JP1 shunt boxes, J7 shroud outline + key notch + pin 1."""
import sys, pcbnew
mm, M = pcbnew.FromMM, pcbnew.ToMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
src, dst = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(src)
W, H = 160, 105
def bb(it):
    r = it.GetBoundingBox(); return (M(r.GetX()), M(r.GetY()), M(r.GetRight()), M(r.GetBottom()))
def hit(a, c, g): return a[0] < c[2] + g and a[2] > c[0] - g and a[1] < c[3] + g and a[3] > c[1] - g
pads, silk = [], []
for f in b.GetFootprints():
    for p in f.Pads():
        if p.IsOnLayer(pcbnew.F_Cu) or p.IsOnLayer(pcbnew.F_Mask): pads.append(bb(p))
def refresh_silk():
    silk.clear()
    for f in b.GetFootprints():
        for it in list(f.GraphicalItems()) + [f.Reference(), f.Value()]:
            if it.GetLayer() == pcbnew.F_SilkS and (not hasattr(it, 'IsVisible') or it.IsVisible()): silk.append(bb(it))
    for d in b.GetDrawings():
        if d.GetLayer() == pcbnew.F_SilkS: silk.append(bb(d))
def strip(ref):
    f = b.FindFootprintByReference(ref)
    for it in list(f.GraphicalItems()):
        if it.GetLayer() == pcbnew.F_SilkS: f.Remove(it)
def seg(pts, w=0.15, closed=False):
    pts = pts + ([pts[0]] if closed else [])
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.F_SilkS)
        s.SetStart(V(x1, y1)); s.SetEnd(V(x2, y2)); s.SetWidth(mm(w)); b.Add(s)
def circle(x, y, r, fill=True):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_CIRCLE); s.SetLayer(pcbnew.F_SilkS)
    s.SetCenter(V(x, y)); s.SetEnd(V(x + r, y)); s.SetWidth(mm(0.15)); s.SetFilled(fill); b.Add(s)
def text(t, x, y, h=0.8, th=0.15, just='c', bold=False, rot=0, w=None):
    o = pcbnew.PCB_TEXT(b); o.SetText(t); o.SetLayer(pcbnew.F_SilkS)
    o.SetTextSize(V(w or h, h)); o.SetTextThickness(mm(th)); o.SetBold(bold)
    o.SetHorizJustify({'l': pcbnew.GR_TEXT_H_ALIGN_LEFT, 'r': pcbnew.GR_TEXT_H_ALIGN_RIGHT, 'c': pcbnew.GR_TEXT_H_ALIGN_CENTER}[just])
    o.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER); o.SetTextAngle(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
    o.SetPosition(V(x, y)); b.Add(o); return o
def place(t, cands, h, th, just='c', rot=0, gp=0.2, gs=0.12, w=None):
    """first candidate whose text box clears pads, existing silk and the board edge"""
    for (x, y) in cands:
        o = text(t, x, y, h, th, just, rot=rot, w=w); r = bb(o)
        if r[0] > 0.3 and r[1] > 0.3 and r[2] < W - 0.3 and r[3] < H - 0.3 \
                and not any(hit(r, p, gp) for p in pads) and not any(hit(r, s, gs) for s in silk):
            silk.append(r); return (x, y)
        b.Remove(o)
    raise SystemExit(f"no room for {t}")
def move_ref(ref, cands):
    t = b.FindFootprintByReference(ref).Reference()
    for (x, y) in cands:
        t.SetPosition(V(x, y)); r = bb(t)
        if not any(hit(r, p, 0.15) for p in pads) and not any(hit(r, s_, 0.08) for s_ in silk) and r[3] < H - 0.3:
            silk.append(r); return (x, y)
    raise SystemExit("no room for ref " + ref)
refresh_silk()
out = []
# --- J1 input / J2 output polarity (outside the plug body so it stays visible after assembly)
for ref, lab in (('J1', 'VIN'), ('J2', 'VOUT')):
    f = b.FindFootprintByReference(ref); body = bb(f)
    for p in f.Pads():
        sign = '+' if p.GetNumber() == '1' else '-'
        px, py = M(p.GetPosition().x), M(p.GetPosition().y)
        if ref == 'J1': xs = [body[2] + 0.4 + k * 0.3 for k in range(8)]; just = 'l'
        else: xs = [body[0] - 0.4 - k * 0.3 for k in range(8)]; just = 'r'
        cands = [(x, py + dy) for dy in (0, -0.8, 0.8, -1.4, 1.4) for x in xs]
        if ref == 'J2':   # no room on the left (RSH1): + below the body (pin 1 side), - above it (pin 2 side)
            yy = body[3] + 0.75 if sign == '+' else body[1] - 0.85
            yy2 = body[3] + 1.9 if sign == '+' else body[1] - 1.9
            cands = [(px + dx, y_) for y_ in (yy, yy2) for dx in (0, -1, 1, -2, 2, 3, 4, 5, 6, 7, 7.5, 8)]; just = 'c'
            if sign == '-': cands = [(x_, y_) for y_ in (43.95, 43.8) for x_ in (156.0, 156.3, 156.6, 157.0)]
        out.append((ref, sign, place(f"{lab}{sign}", cands, 1.0, 0.2, just)))
def _drop(ref):
    r = bb(b.FindFootprintByReference(ref).Reference())
    if r in silk: silk.remove(r)
_drop('D3')
out.append(('D3 ref', move_ref('D3', [(150.0, 80.5), (147.2, 78.0), (151.2, 80.5), (147.3, 79.6)])))
# --- J3/J4 CAN pin names, right-aligned just left of the header outline
names = {'CANH': 'CAN_H', 'CANL': 'CAN_L', 'GND_ISO': 'CAN_GND'}
for ref in ('J3', 'J4'):
    f = b.FindFootprintByReference(ref); body = bb(f)
    for p in f.Pads():
        px, py = M(p.GetPosition().x), M(p.GetPosition().y)
        cands = [(body[0] - 0.25 - k * 0.3, py + dy) for dy in (0, -0.15, -0.3) for k in range(10)]
        if p.GetNetname() == 'GND_ISO':   # J3: D3 sits left of pin 3 -> put it under the header (same for J4, consistent)
            fb = b.FindFootprintByReference(ref); gb = max(r[3] for r in [bb(it) for it in fb.GraphicalItems() if it.GetLayer() == pcbnew.F_SilkS])
            cands = [(px - 0.6 + dx, gb + 0.85) for dx in (0, -0.4, -0.8, 0.4)]
            out.append((ref, p.GetNumber(), place(names[p.GetNetname()], cands, 0.8, 0.15, 'c', gp=0.15, gs=0.08, w=0.65))); continue
        out.append((ref, p.GetNumber(), place(names[p.GetNetname()], cands, 0.8, 0.15, 'r', gp=0.15, gs=0.08, w=0.65)))
# --- JP1: one box per shunt position (1-2 and 3-4) so the jumper direction is obvious
strip('JP1')
f = b.FindFootprintByReference('JP1')
P = {p.GetNumber(): (M(p.GetPosition().x), M(p.GetPosition().y)) for p in f.Pads()}
x0, x1 = P['1'][0] - 1.33, P['2'][0] + 1.33
for a in ('1', '3'):
    y = P[a][1]; r = 1.15
    seg([(x0, y - r), (x1, y - r), (x1, y + r), (x0, y + r)], closed=True)
circle(x0 - 0.55, P['1'][1], 0.25)                     # pin-1 dot
refresh_silk()
_drop('JP1')
yb = P['3'][1] + 1.15
out.append(('JP1 ref', move_ref('JP1', [((x0 + x1) / 2, yb + 0.85), ((x0 + x1) / 2, yb + 1.1), (x0 - 1.6, P['1'][1] + 1.27)])))
out.append(('TERM', place('CAN TERM', [(x1 + 0.35, (P['1'][1] + P['3'][1]) / 2 + d) for d in (0, -0.3, -0.6, -0.8, 0.3)], 0.8, 0.15, 'l', gp=0.15, gs=0.08, w=0.65)))
# --- J7: shroud outline with key notch on the odd-pin side, pin-1 dot and "1"
strip('J7')
f = b.FindFootprintByReference('J7')
P = {p.GetNumber(): (M(p.GetPosition().x), M(p.GetPosition().y)) for p in f.Pads()}
padbb = [bb(p) for p in f.Pads()]
L = min(r[0] for r in padbb) - 0.45; R = max(r[2] for r in padbb) + 0.45
T = min(r[1] for r in padbb) - 0.6; Bt = max(r[3] for r in padbb) + 0.6
yc = P['5'][1]; n = 0.9                                  # notch half-height, centred on the odd column
seg([(L, yc - n), (L, T), (R, T), (R, Bt), (L, Bt), (L, yc + n)])
seg([(L, yc - n), (L - 0.7, yc - n), (L - 0.7, yc + n), (L, yc + n)])
circle(L - 0.55, P['1'][1], 0.3)
refresh_silk()
place('1', [(L - 1.5, P['1'][1]), (L - 1.6, P['1'][1]), (L - 0.55, T - 0.7), (L - 1.3, P['1'][1]), (L - 0.6, T - 1.2)], 0.8, 0.15, 'c', gp=0.15, gs=0.08)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(dst, b)
for o in out: print(o)

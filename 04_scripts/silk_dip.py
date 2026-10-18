"""SW1 address DIP: A0..A5 under each switch, 'ON = 1' note (ON pulls ADDRn low, firmware address = ~ADDR[5:0])."""
import sys, pcbnew
mm, M = pcbnew.FromMM, pcbnew.ToMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
b = pcbnew.LoadBoard(sys.argv[1]); W, H = 160, 105
def bb(it): r = it.GetBoundingBox(); return (M(r.GetX()), M(r.GetY()), M(r.GetRight()), M(r.GetBottom()))
def hit(a, c, g): return a[0] < c[2] + g and a[2] > c[0] - g and a[1] < c[3] + g and a[3] > c[1] - g
pads = [bb(p) for f in b.GetFootprints() for p in f.Pads() if p.IsOnLayer(pcbnew.F_Cu) or p.IsOnLayer(pcbnew.F_Mask)]
silk = []
for f in b.GetFootprints():
    for it in list(f.GraphicalItems()) + [f.Reference(), f.Value()]:
        if it.GetLayer() == pcbnew.F_SilkS and (not hasattr(it, 'IsVisible') or it.IsVisible()): silk.append(bb(it))
for d in b.GetDrawings():
    if d.GetLayer() == pcbnew.F_SilkS: silk.append(bb(d))
def place(t, cands, h=0.8, w=None, just='c'):
    for x, y in cands:
        o = pcbnew.PCB_TEXT(b); o.SetText(t); o.SetLayer(pcbnew.F_SilkS); o.SetTextSize(V(w or h, h)); o.SetTextThickness(mm(0.15))
        o.SetHorizJustify({'c': pcbnew.GR_TEXT_H_ALIGN_CENTER, 'l': pcbnew.GR_TEXT_H_ALIGN_LEFT, 'r': pcbnew.GR_TEXT_H_ALIGN_RIGHT}[just])
        o.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER); o.SetPosition(V(x, y)); b.Add(o); r = bb(o)
        if r[0] > .3 and r[1] > .3 and r[2] < W - .3 and r[3] < H - .3 and not any(hit(r, p, .15) for p in pads) and not any(hit(r, s, .08) for s in silk):
            silk.append(r); return (round(x, 2), round(y, 2))
        b.Remove(o)
    raise SystemExit('no room for ' + t)
f = b.FindFootprintByReference('SW1')
out = []
# R80's reference sits right where A0 goes: move it to the first free spot left/up of R80
r80 = b.FindFootprintByReference('R80'); t80 = r80.Reference(); silk.remove(bb(t80))
cx, cy = M(r80.GetPosition().x), M(r80.GetPosition().y)
for (x, y) in [(cx, cy + 1.3), (cx - 0.3, cy + 1.3), (cx, cy - 1.3), (cx - 2.3, cy), (cx - 2.5, cy + 0.6), (cx - 2.5, cy - 0.6), (cx + 0.5, cy - 1.3)]:
    t80.SetPosition(V(x, y)); r = bb(t80)
    if not any(hit(r, p, .15) for p in pads) and not any(hit(r, s_, .08) for s_ in silk): silk.append(r); out.append(('R80 ref', x, y)); break
else: raise SystemExit('R80 ref')
for p in sorted(f.Pads(), key=lambda p: int(p.GetNumber())):
    n = p.GetNetname()
    if not n.startswith('ADDR'): continue
    x, y = M(p.GetPosition().x), M(p.GetPosition().y)
    top = min(bb(q)[1] for q in f.Pads()); bot = max(bb(q)[3] for q in f.Pads())
    yt = top - 0.15 - 0.75; yb = bot + 0.15 + 0.75          # above the GND pad row / under the ADDR row
    out.append(place('A' + n[4:], [(x, yt - d) for d in (0, 0.15, 0.3)] + [(x, yb + d) for d in (0, 0.15, 0.3)]))
body = bb(f)
pr = f.Reference(); pr.SetVisible(True)
yt = min(bb(q)[1] for q in f.Pads()) - 0.15 - 0.75
out.append(('ON', place('ON=1', [(body[2] + 0.3, yt - d) for d in (0, 0.15, 0.3)] + [(body[0] - 0.3, yt - d) for d in (0, 0.15)], just='l', w=0.7)))
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[2], b)
print(out)

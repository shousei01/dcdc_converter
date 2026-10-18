"""Rev D2: T1 footprint to vendor bobbin (row pitch 25.4 mm, body 27x29). Drag T1 track ends to the new pads;
nudge CR1-CR6 0.4 mm left and Q7/Q8 0.5 mm right so courtyards clear the 29 mm bobbin."""
import sys, pcbnew
mm, M = pcbnew.FromMM, pcbnew.ToMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
b = pcbnew.LoadBoard(sys.argv[1])
def drag_map(moves):
    """moves: {(x,y): (nx,ny)} -> track/via endpoints within 0.02 mm follow"""
    for t in b.GetTracks():
        pts = [('p', t.GetPosition())] if t.Type() == pcbnew.PCB_VIA_T else [('s', t.GetStart()), ('e', t.GetEnd())]
        for k, v in pts:
            q = (round(M(v.x), 2), round(M(v.y), 2))
            for (ox, oy), (nx, ny) in moves.items():
                if abs(q[0] - ox) < 0.02 and abs(q[1] - oy) < 0.02:
                    getattr(t, {'p': 'SetPosition', 's': 'SetStart', 'e': 'SetEnd'}[k])(V(nx, ny))
# --- T1 swap
old = b.FindFootprintByReference('T1')
pos, ang = old.GetPosition(), old.GetOrientation()
oldpads = {(round(M(p.GetPosition().x), 2), round(M(p.GetPosition().y), 2)): p.GetNetname() for p in old.Pads()}
net_of = {p.GetNumber(): p.GetNetname() for p in old.Pads()}
new = pcbnew.FootprintLoad('/home/claude/dcdc/out/custom_fp.pretty', 'TX_PQ2620_12P')
new.SetParent(b); b.Add(new)
new.SetFPIDAsString('custom_fp:TX_PQ2620_12P') if hasattr(new, 'SetFPIDAsString') else None
new.SetPosition(pos); new.SetOrientation(ang)
new.SetReference('T1'); new.SetValue(old.GetValue()); new.SetPath(old.GetPath())
new.Reference().SetPosition(old.Reference().GetPosition()); new.Reference().SetTextAngle(old.Reference().GetTextAngle())
new.Value().SetVisible(False)
for p in new.Pads(): p.SetNet(b.FindNet(net_of[p.GetNumber()]))
newpads = [(round(M(p.GetPosition().x), 2), round(M(p.GetPosition().y), 2), p.GetNetname()) for p in new.Pads()]
b.Remove(old)
moves = {}
for (ox, oy), n in oldpads.items():
    c = min((q for q in newpads if q[2] == n), key=lambda q: abs(q[1] - oy) + abs(q[0] - ox))
    moves[(ox, oy)] = (c[0], c[1])
print('T1 pads', moves)
for (ox, oy), (nx, ny) in moves.items():      # short stubs from the old pad centre to the new pad
    for t in list(b.GetTracks()):
        if t.Type() == pcbnew.PCB_VIA_T: continue
        for v in (t.GetStart(), t.GetEnd()):
            if abs(M(v.x) - ox) < 0.02 and abs(M(v.y) - oy) < 0.02:
                s_ = pcbnew.PCB_TRACK(b); s_.SetStart(V(ox, oy)); s_.SetEnd(V(nx, ny)); s_.SetWidth(t.GetWidth())
                s_.SetLayer(t.GetLayer()); s_.SetNet(t.GetNet()); b.Add(s_)
# --- nudge neighbours
def nudge(ref, dx):
    f = b.FindFootprintByReference(ref)
    mv = {(round(M(p.GetPosition().x), 2), round(M(p.GetPosition().y), 2)): None for p in f.Pads()}
    mv = {k: (round(k[0] + dx, 3), k[1]) for k in mv}
    f.Move(V(dx, 0)); drag_map(mv)

pt = lambda v: (round(M(v.x), 2), round(M(v.y), 2))
def find(net, L, a, c):
    for t in b.GetTracks():
        if t.Type() != pcbnew.PCB_VIA_T and t.GetNetname() == net and t.GetLayer() == L and {pt(t.GetStart()), pt(t.GetEnd())} == {a, c}: return t
    raise SystemExit(f"missing {net} {a} {c}")
def trk(net, L, w, pts):
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(V(x1, y1)); t.SetEnd(V(x2, y2)); t.SetWidth(mm(w)); t.SetLayer(L); t.SetNet(b.FindNet(net)); b.Add(t)
I2 = pcbnew.In2_Cu
# VBUS on In2: leave from the new centre-tap pad, step clear of the SR_D1 pad
dead = [find('VBUS', I2, (81.25, 33.75), (90.38, 42.88)), find('VBUS', I2, (81.25, 33.75), (82.7, 33.75))]
# gate-drive pair LLC_HI_P / LLC_LO_P on In2: shift the diagonal 0.6 mm away from T1 pin 1
dead += [find('LLC_HI_P', I2, (42.02, 28.06), (61.12, 47.15)), find('LLC_LO_P', I2, (43.3, 29.97), (60.62, 47.29)),
         find('LLC_LO_P', I2, (60.62, 47.29), (60.62, 47.39)), find('LLC_LO_P', I2, (60.62, 47.39), (60.51, 47.5))]
le_true = None
lo_v = find('LLC_LO_P', I2, (60.51, 47.5), (60.51, 77.03))
hi_v = find('LLC_HI_P', I2, (61.12, 47.15), (61.12, 73.94))
X = lambda v: (M(v.x), M(v.y))
hs, he = sorted([X(dead[2].GetStart()), X(dead[2].GetEnd())])          # exact HI diagonal ends
ls, le = sorted([X(dead[3].GetStart()), X(dead[3].GetEnd())])          # exact LO diagonal ends
lo_top = X(lo_v.GetStart()) if X(lo_v.GetStart())[1] < X(lo_v.GetEnd())[1] else X(lo_v.GetEnd())
for t in dead: b.Remove(t)
trk('VBUS', I2, 1.5, [(82.7, 33.75), (85.9, 36.95), (85.9, 38.4), (90.38, 42.88)])
J = 0.425                                   # 0.6 mm perpendicular step away from T1 pin 1
cH, cL = hs[0] - hs[1], ls[0] - ls[1]       # lines y = x - c
xlo = 50.0; xhi = 51.6                      # LO steps first (outer line), then HI
yend_lo = le[1]; yend_hi = he[1]
lo_pts = [ls, (xlo, xlo - cL), (xlo - J, xlo - cL + J)]
lo_pts.append((yend_lo + cL - 2 * J, yend_lo))                # back on 45 deg, offset line y = x - cL + 2J
lo_pts.append((lo_top[0], yend_lo + lo_top[0] - lo_pts[-1][0])) # 45 deg down onto the LO vertical
trk('LLC_LO_P', I2, 0.25, lo_pts)
(lo_v.SetStart if X(lo_v.GetStart()) == lo_top else lo_v.SetEnd)(V(*lo_pts[-1]))
hv_top = X(hi_v.GetStart()) if X(hi_v.GetStart())[1] < X(hi_v.GetEnd())[1] else X(hi_v.GetEnd())
hi_pts = [hs, (xhi, xhi - cH), (xhi - J, xhi - cH + J), (yend_hi + cH - 2 * J, yend_hi)]
hi_pts.append((hv_top[0], yend_hi + hv_top[0] - hi_pts[-1][0]))
trk('LLC_HI_P', I2, 0.25, hi_pts)
(hi_v.SetStart if X(hi_v.GetStart()) == hv_top else hi_v.SetEnd)(V(*hi_pts[-1]))
print('LO', [tuple(round(c, 3) for c in q) for q in lo_pts]); print('HI', [tuple(round(c, 3) for c in q) for q in hi_pts])
# neighbours: CR1-6 0.4 mm left, Q7/Q8 0.15 mm right (courtyards clear the 29 mm bobbin); stubs keep the routing
def nudge(ref, dx):
    f = b.FindFootprintByReference(ref)
    olds = [(round(M(p.GetPosition().x), 2), round(M(p.GetPosition().y), 2)) for p in f.Pads()]
    f.Move(V(dx, 0))
    for (ox, oy) in olds:
        for t in list(b.GetTracks()):
            if t.Type() == pcbnew.PCB_VIA_T: continue
            if any(abs(M(v.x) - ox) < 0.02 and abs(M(v.y) - oy) < 0.02 for v in (t.GetStart(), t.GetEnd())):
                s_ = pcbnew.PCB_TRACK(b); s_.SetStart(V(ox, oy)); s_.SetEnd(V(ox + dx, oy)); s_.SetWidth(min(t.GetWidth(), mm(1.0)))
                s_.SetLayer(t.GetLayer()); s_.SetNet(t.GetNet()); b.Add(s_); break
for r in ('CR1', 'CR2', 'CR3', 'CR4', 'CR5', 'CR6'): nudge(r, -0.4)
for r in ('Q7', 'Q8'): nudge(r, 0.1)
for r in ('C2', 'C3', 'C4'):                     # no room left of the caps any more: reference stays on F.Fab only
    b.FindFootprintByReference(r).Reference().SetVisible(False)
t_ = b.FindFootprintByReference('T1').Reference(); t_.SetPosition(V(76.0, 18.0)); t_.SetTextAngle(pcbnew.EDA_ANGLE(0, pcbnew.DEGREES_T))
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[2], b)

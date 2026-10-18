"""Room for a PQ2625 bobbin (29.8 x 26.7 mm base) at T1, same pin pattern.
- T1: new outline/courtyard (+-14.9 body), 1.2 mm holes, moved 0.1 mm right (stubs to the old track ends)
- CR1-CR6 another 0.3 mm left (total 0.7); HB_SW driver-return trace beside them 1.5 -> 0.8 mm
- Q7/Q8 another 0.58 mm right (total 0.68) together with their local fan-out (gate, GND vias);
  GND bus at x=92.3 to x=92.9, Q8 source-to-C2 GND strap 2.5 -> 1.6 mm; R61 0.3 mm right"""
import sys, pcbnew
mm, M = pcbnew.FromMM, pcbnew.ToMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
b = pcbnew.LoadBoard(sys.argv[1])
P = lambda v: (round(M(v.x), 3), round(M(v.y), 3))
def stub_move(f, dx, dy=0.0):
    olds = [P(p.GetPosition()) for p in f.Pads() if p.GetNetname()]
    f.Move(V(dx, dy))
    for (ox, oy) in olds:
        for t in list(b.GetTracks()):
            if t.Type() == pcbnew.PCB_VIA_T: continue
            if any(abs(M(v.x) - ox) < 0.02 and abs(M(v.y) - oy) < 0.02 for v in (t.GetStart(), t.GetEnd())):
                s_ = pcbnew.PCB_TRACK(b); s_.SetStart(V(ox, oy)); s_.SetEnd(V(ox + dx, oy + dy)); s_.SetWidth(t.GetWidth())
                s_.SetLayer(t.GetLayer()); s_.SetNet(t.GetNet()); b.Add(s_); break
def region_move(ref, dx, box):
    """move a footprint and every track end / via inside box with it (segments half inside get stretched)"""
    x0, y0, x1, y1 = box
    inside = lambda q: x0 <= q[0] <= x1 and y0 <= q[1] <= y1
    b.FindFootprintByReference(ref).Move(V(dx, 0))
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            q = P(t.GetPosition())
            if inside(q): t.SetPosition(V(q[0] + dx, q[1]))
            continue
        for get, set_ in ((t.GetStart, t.SetStart), (t.GetEnd, t.SetEnd)):
            q = P(get())
            if inside(q): set_(V(q[0] + dx, q[1]))
def tracks(net, L=pcbnew.F_Cu):
    return [t for t in b.GetTracks() if t.Type() != pcbnew.PCB_VIA_T and t.GetNetname() == net and t.GetLayer() == L]
# --- T1: geometry refresh + 0.1 mm right
old = b.FindFootprintByReference('T1')
pos, ang, path, val, refpos = old.GetPosition(), old.GetOrientation(), old.GetPath(), old.GetValue(), old.Reference().GetPosition()
net_of = {p.GetNumber(): p.GetNetname() for p in old.Pads()}
new = pcbnew.FootprintLoad('/home/claude/dcdc/out/custom_fp.pretty', 'TX_PQ2620_12P')
new.SetParent(b); b.Add(new); new.SetPosition(pos); new.SetOrientation(ang)
new.SetReference('T1'); new.SetValue(val); new.SetPath(path); new.Value().SetVisible(False); new.Reference().SetPosition(refpos)
for p in new.Pads(): p.SetNet(b.FindNet(net_of[p.GetNumber()]))
b.Remove(old)
stub_move(b.FindFootprintByReference('T1'), 0.1)
# --- CR column
for t in tracks('HB_SW'):
    if M(t.GetWidth()) > 1.4 and all(48.5 < M(v.x) < 50.5 and 18 < M(v.y) < 25.5 for v in (t.GetStart(), t.GetEnd())):
        t.SetWidth(mm(0.8))
for r in ('CR1', 'CR2', 'CR3', 'CR4', 'CR5', 'CR6'): stub_move(b.FindFootprintByReference(r), -0.3)
# --- SR FETs: GND bus out of the way first, then move each FET with its local fan-out
for t in tracks('GND'):
    for get, set_ in ((t.GetStart, t.SetStart), (t.GetEnd, t.SetEnd)):
        q = P(get())
        if abs(q[0] - 92.3) < 0.02 and 32.7 < q[1] < 40.2: set_(V(92.72, q[1]))
for t in tracks('GND'):
    if abs(M(t.GetStart().x) - 92.3) < 0.02 and abs(M(t.GetEnd().x) - 92.3) < 0.02: t.SetWidth(mm(0.8))
for t in tracks('GND'):
    if {P(t.GetStart()), P(t.GetEnd())} == {(90.9, 22.405), (89.97, 26.2)} or \
       {(round(M(t.GetStart().x), 2), round(M(t.GetStart().y), 2)), (round(M(t.GetEnd().x), 2), round(M(t.GetEnd().y), 2))} == {(90.9, 22.41), (89.97, 26.2)}:
        t.SetWidth(mm(1.6))
region_move('Q8', 0.58, (84.4, 17.6, 91.7, 23.4))
region_move('Q7', 0.58, (84.4, 36.6, 91.7, 42.4))
# GND stitching vias next to the FET source pads: step them out of the pads (x 91.83 -> 92.2);
# the ones at Q7 pin 3 and Q8 pins 2-3 would crowd the G7/G8 inner-layer traces, so they go (pins 1-3 are tied by the 0.6 mm strap)
vmove = {(91.83, y): (92.2, y) for y in (19.86, 40.13, 41.41)}
gone = {(91.83, 38.87), (91.83, 21.14), (91.83, 22.41)}
for t in list(b.GetTracks()):
    if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == 'GND':
        q = (round(M(t.GetPosition().x), 2), round(M(t.GetPosition().y), 2))
        if q in vmove: t.SetPosition(V(*vmove[q]))
        elif q in gone: b.Remove(t)
for t in list(b.GetTracks()):
    if t.Type() == pcbnew.PCB_VIA_T or t.GetNetname() != 'GND': continue
    for get, set_ in ((t.GetStart, t.SetStart), (t.GetEnd, t.SetEnd)):
        q = (round(M(get().x), 2), round(M(get().y), 2))
        if q in vmove: set_(V(*vmove[q]))
for t in list(b.GetTracks()):
    if t.Type() != pcbnew.PCB_VIA_T and t.GetNetname() == 'GND' and any((round(M(v.x), 2), round(M(v.y), 2)) in gone for v in (t.GetStart(), t.GetEnd())):
        b.Remove(t)
region_move('R61', 0.3, (85.0, 12.0, 87.4, 16.7))
r_ = b.FindFootprintByReference('R64').Reference(); r_.SetPosition(r_.GetPosition() + V(-0.7, 0))
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[2], b)

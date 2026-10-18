"""Move JP1 down 5.08 mm (frees room for the J4 CAN labels) and re-route its four nets."""
import sys, pcbnew
mm, M = pcbnew.FromMM, pcbnew.ToMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
b = pcbnew.LoadBoard(sys.argv[1]); D = 5.08
f = b.FindFootprintByReference('JP1'); f.Move(V(0, D))
P = {p.GetNumber(): (round(M(p.GetPosition().x), 2), round(M(p.GetPosition().y), 2)) for p in f.Pads()}
for d in list(b.GetDrawings()):
    if isinstance(d, pcbnew.PCB_TEXT) and d.GetText().startswith('TERM'): b.Remove(d)
pt = lambda v: (round(M(v.x), 2), round(M(v.y), 2))
kill = [((146.88, 92.11), (144.32, 92.11), 'CANL', 'F.Cu'), ((147.15, 88.6), (146.88, 89.57), 'CAN_TH', 'F.Cu'),
        ((150.9, 90.63), (149.42, 92.11), 'CAN_TL', 'In2.Cu'), ((150.9, 88.0), (150.9, 90.63), 'CAN_TL', 'In2.Cu'),
        ((146.88, 92.11), (148.37, 93.6), 'CANL', 'In2.Cu'), ((148.37, 93.6), (151.5, 93.6), 'CANL', 'In2.Cu'),
        ((151.5, 93.6), (154.65, 90.45), 'CANL', 'In2.Cu'), ((154.65, 90.45), (154.65, 88.54), 'CANL', 'In2.Cu'),
        ((149.42, 83.37), (149.42, 89.57), 'CANH', 'B.Cu')]
n = 0
for t in list(b.GetTracks()):
    if t.Type() == pcbnew.PCB_VIA_T: continue
    k = (pt(t.GetStart()), pt(t.GetEnd()), t.GetNetname(), b.GetLayerName(t.GetLayer()))
    if k in kill or (k[1], k[0], k[2], k[3]) in kill: b.Remove(t); n += 1
assert n == len(kill), n
def trk(net, L, w, pts):
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(V(x1, y1)); t.SetEnd(V(x2, y2)); t.SetWidth(mm(w)); t.SetLayer(L); t.SetNet(b.FindNet(net)); b.Add(t)
print(P)
trk('CAN_TH', pcbnew.F_Cu, 0.2, [(147.15, 88.6), (147.15, P['1'][1] - 0.95), P['1']])
trk('CANL', pcbnew.F_Cu, 0.5, [(144.32, 92.11), (144.32, 95.8), (145.71, P['3'][1]), P['3']])
trk('CANH', pcbnew.B_Cu, 0.3, [(149.42, 83.37), P['2']])
trk('CAN_TL', pcbnew.In2_Cu, 0.25, [(150.9, 88.0), (150.9, P['4'][1] - 1.48), P['4']])
y = P['3'][1] + 1.49
trk('CANL', pcbnew.In2_Cu, 0.5, [P['3'], (P['3'][0] + 1.49, y), (151.5, y), (151.5 + (y - 95.53), 95.53), (154.65, 95.53), (154.65, 88.54)])
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[2], b)

import json, pcbnew
mm, M = pcbnew.FromMM, pcbnew.ToMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
b = pcbnew.LoadBoard('/home/claude/dcdc/pcb4/final_d1.kicad_pcb')
up = json.load(open('/home/claude/dcdc/sch3/uuid_paths.json'))
for f in b.GetFootprints():
    f.SetPath(pcbnew.KIID_PATH(up[f.GetReference()]))
# new net
ni = pcbnew.NETINFO_ITEM(b, "CAN_TH"); b.Add(ni)
net = lambda n: b.FindNet(n)
# replace JP1
old = b.FindFootprintByReference('JP1')
new = pcbnew.FootprintLoad('/usr/share/kicad/footprints/Connector_PinHeader_2.54mm.pretty', 'PinHeader_2x02_P2.54mm_Vertical')
new.SetParent(b)
b.Add(new)
new.SetPosition(V(146.88, 89.57))
new.SetReference('JP1'); new.SetValue('TERM'); new.SetPath(pcbnew.KIID_PATH(up['JP1']))
for attr in ('GetFieldByName',):
    pass
new.Reference().SetTextSize(old.Reference().GetTextSize()); new.Reference().SetTextThickness(old.Reference().GetTextThickness())
new.Reference().SetPosition(V(146.88 + 1.27, 87.6)); new.Reference().SetVisible(True)
new.Value().SetLayer(pcbnew.F_Fab); new.Value().SetVisible(False)
b.Remove(old)
for p in new.Pads():
    p.SetNet(net({"1": "CAN_TH", "2": "CANH", "3": "CANL", "4": "CAN_TL"}[p.GetNumber()]))
    print('JP1', p.GetNumber(), p.GetNetname(), M(p.GetPosition().x), M(p.GetPosition().y))
b.FindFootprintByReference('R30').FindPadByNumber('1').SetNet(net('CAN_TH'))
# remove obsolete tracks
def pt(v): return (round(M(v.x), 2), round(M(v.y), 2))
kill = []
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T: continue
    n, L, s, e = t.GetNetname(), t.GetLayer(), pt(t.GetStart()), pt(t.GetEnd())
    if n == 'CANH' and L == pcbnew.F_Cu and {s, e} <= {(149.06, 77.05), (148.33, 77.79), (147.59, 78.53), (147.59, 80.72), (145.75, 82.56)} and not (s == (154.11, 72.0) or e == (154.11, 72.0)):
        kill.append(t)
    if n == 'CAN_TL' and L == pcbnew.In2_Cu: kill.append(t)
    if n == 'CANL' and L == pcbnew.In2_Cu and {s, e} == {(146.88, 92.11), (151.08, 92.11)}: kill.append(t)
    if n == 'CANL' and L == pcbnew.In2_Cu and {s, e} == {(151.08, 92.11), (154.65, 88.54)}: kill.append(t)
    if n == 'CANH' and L == pcbnew.B_Cu and {s, e} == {(152.01, 83.37), (140.92, 83.37)}: split = t
for t in set(kill):
    print('del', t.GetNetname(), b.GetLayerName(t.GetLayer()), pt(t.GetStart()), pt(t.GetEnd())); b.Remove(t)
def trk(n, L, w, pts):
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(V(x1, y1)); t.SetEnd(V(x2, y2)); t.SetWidth(mm(w)); t.SetLayer(L); t.SetNet(net(n)); b.Add(t)
# split B.Cu CANH at x=149.42
a, c = pt(split.GetStart()), pt(split.GetEnd())
split.SetEnd(V(149.42, 83.37)) if a == (152.01, 83.37) else split.SetStart(V(149.42, 83.37))
trk('CANH', pcbnew.B_Cu, 0.5, [(140.92, 83.37), (149.42, 83.37)] if a == (152.01, 83.37) else [(149.42, 83.37), (152.01, 83.37)])
trk('CANH', pcbnew.B_Cu, 0.3, [(149.42, 83.37), (149.42, 89.57)])
trk('CAN_TH', pcbnew.F_Cu, 0.2, [(145.75, 82.56), (145.75, 83.3), (147.15, 84.7), (147.15, 88.6), (146.88, 89.57)])
trk('CAN_TL', pcbnew.In2_Cu, 0.25, [(148.9, 81.73), (148.9, 86.0), (150.9, 88.0), (150.9, 90.63), (149.42, 92.11)])
trk('CANL', pcbnew.In2_Cu, 0.5, [(146.88, 92.11), (148.37, 93.6), (151.5, 93.6), (154.65, 90.45), (154.65, 88.54)])
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard('/home/claude/dcdc/pcb4/final_d2.kicad_pcb', b)

"""Add the VIN-monitor PWM block to the board (placement + nets); routing is done afterwards by connect/maze.
usage: vinmon.py in out"""
import sys, json, pcbnew
mm, M = pcbnew.FromMM, pcbnew.ToMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
sys.path.insert(0, '/home/claude/dcdc'); import design as D
b = pcbnew.LoadBoard(sys.argv[1])
up = json.load(open('/home/claude/dcdc/sch3/uuid_paths.json'))
P2 = lambda v: (round(M(v.x), 2), round(M(v.y), 2))
# 1) stitching vias (added on the 5 mm grid, no tracks) are removed here; stitch.py re-adds them at the end
pre = pcbnew.LoadBoard('/home/claude/dcdc/opt/o3.kicad_pcb')
keep = {P2(t.GetPosition()) for t in pre.GetTracks() if t.Type() == pcbnew.PCB_VIA_T}
dead = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and P2(t.GetPosition()) not in keep and t.GetNetname() in ('GND', 'GNDP', 'GND_ISO')]
# 2) U12 pin 4 was tied to GNDP: drop those tracks
u12 = b.FindFootprintByReference('U12'); pad4 = [p for p in u12.Pads() if p.GetNumber() == '4'][0]
dead += [t for t in b.GetTracks() if t.Type() != pcbnew.PCB_VIA_T and t.GetNetname() == 'GNDP' and any(pad4.HitTest(v) for v in (t.GetStart(), t.GetEnd()))]
# 3) new nets
for n in ('PE_P', 'PB_P', 'RAMP_P', 'RAMPS_P', 'RST_P', 'GATE_P', 'DIS_P', 'VINPWM_P', 'VIN_PWM'):
    if not b.FindNet(n): b.Add(pcbnew.NETINFO_ITEM(b, n))
net = lambda n: b.FindNet(n)
for t in b.GetTracks():
    if t.GetNetname() == 'SP_PA2': t.SetNet(net('VIN_PWM'))
for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetNetname() == 'SP_PA2': p.SetNet(net('VIN_PWM'))
pad4.SetNet(net('VINPWM_P'))
[p for p in u12.Pads() if p.GetNumber() == '13'][0].SetNet(net('VIN_PWM'))
# 4) place the new parts (empty primary area under the OVP comparator, x 39-64 / y 85-97)
PL = {'C84': (60.0, 86.4, 0), 'U18': (60.0, 89.0, 0), 'R110': (60.0, 91.6, 0), 'R109': (56.9, 89.0, 90), 'R108': (63.1, 88.6, 90),
      'C83': (52.0, 86.4, 0), 'U17': (52.0, 89.0, 0), 'R106': (55.0, 92.0, 0), 'D7': (52.0, 93.6, 0),
      'C81': (49.0, 96.0, 90), 'R107': (50.4, 96.0, 90), 'Q10': (46.6, 95.4, 0), 'R89': (46.6, 92.2, 90),
      'C82': (47.4, 89.0, 90), 'Q9': (43.4, 89.0, 0), 'R86': (43.4, 85.8, 0), 'R87': (40.2, 87.6, 90), 'R88': (40.2, 90.6, 90)}
parts = {p.ref: p for p in D.P}
for ref, (x, y, rot) in PL.items():
    p = parts[ref]; lib, name = D.FP[p.fp].split(':') if ':' not in p.fp else p.fp.split(':')
    fp = pcbnew.FootprintLoad(f'/usr/share/kicad/footprints/{lib}.pretty', name)
    fp.SetParent(b); b.Add(fp)
    fp.SetReference(ref); fp.SetValue(p.value); fp.SetPath(pcbnew.KIID_PATH(up[ref]))
    fp.SetPosition(V(x, y)); fp.SetOrientationDegrees(rot)
    fp.Value().SetLayer(pcbnew.F_Fab); fp.Value().SetVisible(False)
    fp.Reference().SetTextSize(V(0.8, 0.8)); fp.Reference().SetTextThickness(mm(0.12))
    for pd in fp.Pads():
        n = p.pins.get(pd.GetNumber())
        if n: pd.SetNet(net(n))
for f in b.GetFootprints():
    f.SetPath(pcbnew.KIID_PATH(up[f.GetReference()]))
for t in dead: b.Remove(t)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[2], b)
print('removed', len(dead), 'placed', len(PL))

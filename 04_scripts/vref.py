"""Add REF3030 ADC reference (U19 + C85), move VREF+ / R25 / R29 / C36 / C37 to VREF_ADC, rip +3V3A for re-route.
usage: vref.py in out"""
import sys, json, pcbnew
sys.path.insert(0, '/home/claude/dcdc'); import design as D
M = pcbnew.ToMM; mm = pcbnew.FromMM; V = pcbnew.VECTOR2I
b = pcbnew.LoadBoard(sys.argv[1])
up = json.load(open('/home/claude/dcdc/sch3/uuid_paths.json'))
P = {p.ref: p for p in D.P}
def net(n):
    ni = b.FindNet(n)
    if ni is None: ni = pcbnew.NETINFO_ITEM(b, n); b.Add(ni)
    return ni
PL = {'U19': (126.5, 91.75, 0), 'C85': (126.5, 89.0, 0)}
for r, (x, y, a) in PL.items():
    p = P[r]; lib, name = p.fp.split(':')
    fp = pcbnew.FootprintLoad(f'/usr/share/kicad/footprints/{lib}.pretty', name)
    fp.SetReference(r); fp.SetValue(p.value); fp.SetPosition(V(mm(x), mm(y))); fp.SetOrientationDegrees(a)
    b.Add(fp)
kill = [t for t in b.GetTracks() if t.GetNetname() == '+3V3A']
# stitching vias under the new parts
for r in PL:
    f = b.FindFootprintByReference(r); bb = f.GetBoundingBox(False, False)
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'GND':
            x, y = M(t.GetPosition())
            if M(bb.GetX()) - 0.8 < x < M(bb.GetRight()) + 0.8 and M(bb.GetY()) - 0.8 < y < M(bb.GetBottom()) + 0.8: kill.append(t)
for t in set(kill): b.Remove(t)
for f in b.GetFootprints():
    p = P.get(f.GetReference())
    if not p: continue
    for pd in f.Pads():
        n = p.pins.get(pd.GetNumber())
        if n and n != 'NC' and pd.GetNetname() != n: pd.SetNet(net(n))
    if f.GetValue() != p.value and f.GetReference() in ('U19', 'C85'): f.SetValue(p.value)
    f.SetPath(pcbnew.KIID_PATH(up[f.GetReference()]))
print('ripped', len(set(kill)))
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(sys.argv[2])

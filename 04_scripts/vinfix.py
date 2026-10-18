"""Review fix of the VIN monitor (18 Oct): U18 inputs swapped (IN+ = OVP_DIV, IN- = RAMPS_P), R110 4.7M to OVP_DIV,
R109 1k (rotated so RAMPS_P faces U18 pin 3), C81 220p C0G, R107 100k. Rips the affected local tracks for re-routing.
usage: vinfix.py in out"""
import sys, json, pcbnew
sys.path.insert(0, '/home/claude/dcdc'); import design as D
M = pcbnew.ToMM; mm = pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1])
up = json.load(open('/home/claude/dcdc/sch3/uuid_paths.json'))
P = {p.ref: p for p in D.P}
for r in ('U18', 'R110', 'R109', 'C81', 'R107', 'R81', 'U16'):
    f = b.FindFootprintByReference(r); p = P[r]
    f.SetValue(p.value)
    for pd in f.Pads():
        n = p.pins.get(pd.GetNumber())
        if n and pd.GetNetname() != n:
            ni = b.FindNet(n)
            if ni is None: ni = pcbnew.NETINFO_ITEM(b, n); b.Add(ni)
            print('pad', r, pd.GetNumber(), pd.GetNetname(), '->', n); pd.SetNet(ni)
f = b.FindFootprintByReference('R109'); f.SetOrientationDegrees(270)
# rip: all RAMPS_P; RAMP_P and OVP_DIV inside the monitor block; VINPWM_P near R110
kill = []
for t in b.GetTracks():
    n = t.GetNetname(); s, e = M(t.GetStart()), M(t.GetEnd())
    inblk = all(40 <= x <= 64.2 and 84.6 <= y <= 98 for x, y in (s, e))
    if n == 'RAMPS_P' or (n in ('RAMP_P', 'OVP_DIV') and inblk and max(s[0], e[0]) > 55.5) or \
       (n == 'VINPWM_P' and inblk and min(s[1], e[1]) > 90.5):
        kill.append(t)
for t in kill: b.Remove(t)
print('ripped', len(kill))
for f in b.GetFootprints():
    f.SetPath(pcbnew.KIID_PATH(up[f.GetReference()]))
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(sys.argv[2])

"""list ground-net zone fragments (per zone, per layer) that contain no via of their net"""
import sys, pcbnew
sys.path.insert(0, '/home/claude/dcdc/pcb5'); from islands5 import polys
from shapely.geometry import Point, box
M = pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
for net in ('GND', 'GNDP', 'GND_ISO', 'PGND', 'VBUS', 'VOUT', 'VIN', 'SW1', 'SW2', 'HB_SW'):
    vias = [Point(M(t.GetPosition().x), M(t.GetPosition().y)) for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == net]
    for z in b.Zones():
        if z.GetNetname() != net or z.GetIsRuleArea(): continue
        for L in (pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
            if not z.IsOnLayer(L): continue
            for q in polys(z.GetFilledPolysList(L)):
                if any(q.buffer(0.01).contains(v) for v in vias): continue
                pads = [f"{f.GetReference()}.{p.GetNumber()}" for f in b.GetFootprints() for p in f.Pads()
                        if p.GetNetname() == net and p.IsOnLayer(L) and q.buffer(0.02).contains(Point(M(p.GetPosition().x), M(p.GetPosition().y)))]
                print(net, z.GetZoneName(), b.GetLayerName(L), [round(c, 1) for c in q.bounds], round(q.area, 2), pads[:6])

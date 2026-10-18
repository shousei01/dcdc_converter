"""Layout review fixes, step 1 (power path, switch-node copper, gate loops, Kelvin taps).
usage: opt1.py in out"""
import sys, pcbnew
mm, M = pcbnew.FromMM, pcbnew.ToMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
b = pcbnew.LoadBoard(sys.argv[1])
F, I2, B = pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu
P2 = lambda v: (round(M(v.x), 1), round(M(v.y), 1))
def find(net, L, a, c):
    hits = [t for t in b.GetTracks() if t.Type() != pcbnew.PCB_VIA_T and t.GetNetname() == net and t.GetLayer() == L
            and {P2(t.GetStart()), P2(t.GetEnd())} == {a, c}]
    assert hits, (net, a, c); return hits
def via_at(net, p):
    hits = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == net and P2(t.GetPosition()) == p]
    assert hits, (net, p); return hits
def trk(net, L, w, pts):
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(V(x1, y1)); t.SetEnd(V(x2, y2)); t.SetWidth(mm(w)); t.SetLayer(L); t.SetNet(b.FindNet(net)); b.Add(t)
def via(net, x, y, d=0.6, drill=0.3):
    v = pcbnew.PCB_VIA(b); v.SetPosition(V(x, y)); v.SetWidth(mm(d)); v.SetDrill(mm(drill)); v.SetNet(b.FindNet(net)); v.SetLayerPair(F, B); b.Add(v)
def zone(net, poly, prio, name, L=F, clr=0.3):
    z = pcbnew.ZONE(b); z.SetLayer(L); z.SetNet(b.FindNet(net)); ol = z.Outline(); ol.NewOutline()
    for x, y in poly: ol.Append(mm(x), mm(y))
    z.SetLocalClearance(mm(clr)); z.SetMinThickness(mm(0.25)); z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS); z.SetAssignedPriority(prio); z.SetZoneName(name); b.Add(z); return z
def reshape(name, poly):
    z = [z for z in b.Zones() if z.GetZoneName() == name][0]; ol = z.Outline(); ol.RemoveAllContours(); ol.NewOutline()
    for x, y in poly: ol.Append(mm(x), mm(y))
dead = []
# 1) resonant-capacitor column: full-width copper on both sides of CR1..CR6 (10 A rms primary current)
zone('VIN', [(50.3, 13.9), (52.7, 13.9), (52.7, 21.6), (50.3, 21.6)], 30, 'PWR_VIN_CR')
zone('GNDP', [(50.3, 22.0), (52.7, 22.0), (52.7, 29.9), (50.3, 29.9)], 30, 'PWR_GNDP_CR')
reshape('PWR_CR_MID_1', [(53.75, 14.0), (60.2, 14.0), (60.2, 29.8), (53.75, 29.8)])
# 2) output path C11 -> J2 was a single 1.0 mm track: VOUT pour along it
zone('VOUT', [(143.9, 33.0), (146.6, 33.0), (146.6, 52.3), (149.9, 52.3), (149.9, 55.6), (143.9, 55.6)], 28, 'PWR_VOUT_J2')
# 3) 4SBB switch nodes: only the copper the current needs (L1 pad, FET pins/tab and the path between)
reshape('PWR_SW1_10', [(112.45, 12.45), (116.2, 12.45), (116.2, 25.6), (112.6, 33.4), (107.5, 33.4), (107.5, 22.75), (112.45, 22.75)])
reshape('PWR_SW2_11', [(127.8, 12.45), (131.55, 12.45), (131.55, 19.3), (136.4, 19.3), (136.4, 33.4), (131.5, 33.4), (127.8, 25.55)])
# 4a) Q1 high-side gate loop: driver return SW1 runs next to G1 on In2 (was a separate diagonal ~100 mm2 loop)
dead += find('SW1', I2, (105.7, 33.3), (99.5, 39.5)) + find('SW1', I2, (99.5, 39.5), (99.5, 41.3))
dead += via_at('SW1', (105.7, 33.3)) + via_at('SW1', (99.5, 41.3)) + find('SW1', F, (105.7, 32.0), (105.7, 33.3))
via('SW1', 107.0, 30.6); via('SW1', 101.8, 46.9)
trk('SW1', I2, 0.6, [(107.0, 30.6), (107.0, 45.8), (105.9, 46.9), (101.8, 46.9)])
# 4b) Q3 high-side gate loop: G3 0.25 -> 0.5 mm, SW2 return on B.Cu parallel to it from a via at the Q3 source pins
for t in find('G3', B, (135.1, 23.9), (132.4, 46.1)): t.SetWidth(mm(0.5))
dead += find('SW2', I2, (131.3, 42.0), (129.3, 40.0)) + find('SW2', I2, (129.3, 40.0), (129.3, 30.9))
dead += via_at('SW2', (129.3, 30.9)) + find('SW2', F, (134.0, 30.9), (129.3, 30.9))
for t in find('PGND', I2, (137.2, 13.2), (137.2, 35.2)): t.SetWidth(mm(1.0))     # snubber/pull-down return only
for t in find('SW2', I2, (131.3, 42.0), (135.3, 46.0)): t.SetWidth(mm(0.6))   # boot-cap / pull-down return, no power
via('SW2', 136.0, 22.6)
trk('SW2', F, 0.5, [(135.1, 22.6), (136.0, 22.6)])
trk('SW2', B, 0.5, [(136.0, 22.6), (135.94, 24.0), (133.24, 46.2), (135.3, 46.0)])
# 4c) Q5 (LLC high side) gate loop: HB_SW driver return on B.Cu right under the G5 In2 run, into the HB_SW pour next to Q5
dead += find('HB_SW', B, (48.3, 23.1), (56.6, 31.6)) + via_at('HB_SW', (56.6, 31.6)) + find('HB_SW', F, (56.6, 31.6), (56.6, 34.0))
via('HB_SW', 52.9, 33.4)
trk('HB_SW', B, 0.35, [(48.3, 23.09), (50.2, 24.99), (50.2, 30.2), (52.9, 32.9), (52.9, 33.4)])
# 5) Kelvin taps for U8: both sense lines end inside the RSH1 pads
for t in find('GND', F, (140.8, 47.5), (139.2, 47.5)): pass
trk('GND', F, 0.25, [(140.8, 47.49), (141.75, 47.49)])
dead += find('VOUT_N', F, (141.2, 53.2), (140.8, 52.8))
trk('VOUT_N', F, 0.25, [(140.8, 52.76), (141.75, 52.76)])
for t in dead: b.Remove(t)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[2], b)

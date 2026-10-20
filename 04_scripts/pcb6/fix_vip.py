"""Keep via drill holes out of SMD pads (solder wicking): C69.2 / C95.2 (after the Rev E2 courtyard moves),
J7.5 (from Rev E), and R64.1 (annulus touching). U12.2's GNDP via stays: the +5V_P track leaves no room to move it.   usage: fix_vip.py in.kicad_pcb out.kicad_pcb"""
import sys, math, pcbnew
M, mm = pcbnew.ToMM, pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1])
V = lambda p: pcbnew.VECTOR2I(mm(p[0]), mm(p[1]))
P = lambda v: (M(v.x), M(v.y))
close = lambda a, c: math.dist(a, c) < 0.003
def move_via(old, new):
    vs = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and close(P(t.GetPosition()), old)]
    assert len(vs) == 1, old
    vs[0].SetPosition(V(new))
    for t in b.GetTracks():                       # drag attached track ends
        if t.Type() == pcbnew.PCB_TRACE_T and t.GetNetname() == vs[0].GetNetname():
            if close(P(t.GetStart()), old): t.SetStart(V(new))
            if close(P(t.GetEnd()), old): t.SetEnd(V(new))
move_via((92.1, 28.8), (91.8, 28.8))          # C69.2 GND
move_via((58.6, 54.3), (58.6, 53.9))          # C95.2 GNDP
move_via((124.0, 97.6), (122.4, 98.5))        # J7.5 GND: next to the pad, clear of the SWDIO_C bottom-layer run
t = pcbnew.PCB_TRACK(b); t.SetStart(V((122.4, 98.5))); t.SetEnd(V((122.9, 98.0))); t.SetLayer(pcbnew.F_Cu); t.SetWidth(mm(0.3))
t.SetNet(b.FindNet("GND")); b.Add(t)
# R64 0.15 mm up, so its G5 pad clears the Q5 gate via
f = b.FindFootprintByReference("R64"); f.SetPosition(V((54.15, 30.35)))
for t in b.GetTracks():
    if t.Type() != pcbnew.PCB_TRACE_T: continue
    for g, s in ((t.GetStart, t.SetStart), (t.GetEnd, t.SetEnd)):
        e = P(g())
        if t.GetNetname() == "G5" and close(e, (53.64, 30.5)): s(V((53.64, 30.35)))
        if t.GetNetname() == "HB_SW" and close(e, (54.66, 30.5)): s(V((54.66, 30.35)))
        if t.GetNetname() == "HB_SW" and close(e, (55.0, 30.84)): s(V((55.0, 30.69)))
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[2], b)

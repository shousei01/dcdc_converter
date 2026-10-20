"""Rev E2 last step: re-lock the hand-edited power copper (R64 gate link, C34 GND stub) and refill the zones.
usage: finish_e2.py in.kicad_pcb out.kicad_pcb"""
import sys, math, pcbnew
M = pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T: continue
    ends = [(M(t.GetStart().x), M(t.GetStart().y)), (M(t.GetEnd().x), M(t.GetEnd().y))]
    if t.GetNetname() == "G5" and any(math.dist(p, (53.9, 31.0)) < 0.01 or math.dist(p, (53.64, 30.5)) < 0.6 for p in ends): t.SetLocked(True)
    if t.GetNetname() == "GND" and any(math.dist(p, (105.12, 85.65)) < 0.01 for p in ends): t.SetLocked(True)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[2], b)

"""J3 pin 3 (GND_ISO) on In2 sat in a pocket closed by the J3 -> J4 CANH (left) and CANL (right) links, so its only
thermal spoke went into a scrap of fill tied to nothing else (KiCad 8+ DRC: 'thermal relief connection to zone
incomplete'). The J3.2 -> J4.2 CANL link moves to B.Cu (same path, nothing else on B.Cu there): on In2 the pad now
opens to the GND_ISO plane on the right, on B.Cu to the left.   usage: fix_j3.py in.kicad_pcb out.kicad_pcb"""
import sys, pcbnew
M = pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
SEG = [((156.0, 74.54), (156.0, 75.797)), ((156.0, 75.797), (156.55, 75.797)), ((156.55, 75.797), (157.257, 76.504)),
       ((157.257, 76.504), (157.257, 87.769)), ((157.257, 87.769), (156.0, 89.026))]
n = 0
for t in b.GetTracks():
    if t.Type() != pcbnew.PCB_TRACE_T or t.GetNetname() != "CANL" or t.GetLayer() != pcbnew.In2_Cu: continue
    e = {(round(M(t.GetStart().x), 3), round(M(t.GetStart().y), 3)), (round(M(t.GetEnd().x), 3), round(M(t.GetEnd().y), 3))}
    if any(e == set(s) for s in SEG): t.SetLayer(pcbnew.B_Cu); n += 1
assert n == len(SEG), n
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[2], b)
print("moved", n, "CANL segments to B.Cu")

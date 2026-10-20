"""After the E2 re-route: restore the original lock state (pre-routed copper locked, router copper free).
usage: post.py routed.kicad_pcb reference_original.kicad_pcb out.kicad_pcb"""
import sys, pcbnew
M = pcbnew.ToMM
src, ref, dst = sys.argv[1:4]
def key(t):
    s, e = t.GetStart(), t.GetEnd()
    a, b_ = (s.x, s.y), (e.x, e.y)
    return (t.GetNetname(), t.Type() == pcbnew.PCB_VIA_T, t.GetLayer() if t.Type() != pcbnew.PCB_VIA_T else -1, min(a, b_), max(a, b_), t.GetWidth())
r = pcbnew.LoadBoard(ref)
lk = {key(t) for t in r.GetTracks() if t.IsLocked()}
b = pcbnew.LoadBoard(src)
n = 0
for t in b.GetTracks():
    on = key(t) in lk
    t.SetLocked(on); n += on
pcbnew.SaveBoard(dst, b)
print("locked", n)

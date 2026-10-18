"""Clean-ups after the review: (1) ADDR2 had two parallel routes from the router (MCU branch ran alongside the SW1-R34-R40
track) -> the MCU branch now joins that track at its first node; (2) same-net segments lying completely inside another
same-net segment on the same layer are deleted (no copper change). usage: dedup.py in out"""
import sys, collections, pcbnew
from shapely.geometry import LineString
mm, M = pcbnew.FromMM, pcbnew.ToMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
b = pcbnew.LoadBoard(sys.argv[1])
P2 = lambda v: (round(M(v.x), 2), round(M(v.y), 2))
kill = []
for t in b.GetTracks():
    if t.Type() != pcbnew.PCB_VIA_T and t.GetNetname() == 'ADDR2' and t.GetLayer() == pcbnew.F_Cu and \
       {P2(t.GetStart()), P2(t.GetEnd())} in ({(88.35, 95.7), (89.3, 96.65)}, {(89.3, 96.65), (94.85, 96.65)}):
        kill.append(t)
assert len(kill) == 2, len(kill)
n = pcbnew.PCB_TRACK(b); n.SetStart(V(88.35, 95.7)); n.SetEnd(V(89.07, 96.34)); n.SetWidth(mm(0.15)); n.SetLayer(pcbnew.F_Cu)
n.SetNet(b.FindNet('ADDR2')); b.Add(n)
by = collections.defaultdict(list)
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T or t in kill: continue
    a, c = (M(t.GetStart().x), M(t.GetStart().y)), (M(t.GetEnd().x), M(t.GetEnd().y))
    if a == c: kill.append(t); continue
    by[(t.GetNetname(), t.GetLayer())].append((t, LineString([a, c]), M(t.GetWidth())))
gone = set()
for segs in by.values():
    for i, (t1, l1, w1) in enumerate(segs):
        for t2, l2, w2 in segs:
            if t2 is t1 or id(t2) in gone or w2 < w1: continue
            if l1.within(l2.buffer((w2 - w1) / 2 + 1e-3)) and not (w1 == w2 and l1.length > l2.length):
                if w1 == w2 and abs(l1.length - l2.length) < 1e-6 and id(t1) < id(t2): continue   # exact twins: keep one
                kill.append(t1); gone.add(id(t1)); break
print('removed', len(kill))
for t in kill: b.Remove(t)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[2], b)

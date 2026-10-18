"""Replace router staircases with straight / 45-degree segments.
A chain = run of same-net, same-layer, same-width segments whose inner nodes touch nothing else (no via, pad or branch).
Sub-chains are replaced greedily by the longest clear shortcut (45-degree dogleg preferred, else a direct line).
Clearance is checked against every other-net copper on the layer (tracks, pads, vias, power pours, keep-outs) + 0.22 mm.
GND/GNDP/GND_ISO floods are ignored (they re-fill). usage: straighten.py in out"""
import sys, math, collections, pcbnew
from shapely.geometry import LineString, Point, Polygon, box
from shapely.strtree import STRtree
mm, M = pcbnew.FromMM, pcbnew.ToMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
b = pcbnew.LoadBoard(sys.argv[1])
CLR = 0.22
KEEP = {'SW1', 'SW2', 'G1', 'G3', 'HO1', 'HO2', 'HB_SW', 'G5', 'HOP'}      # hand-paired gate-drive loops stay as drawn
LAYERS = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
K = lambda x, y: (round(x, 3), round(y, 3))
def poly_of(sp):
    out = []
    for i in range(sp.OutlineCount()):
        o = sp.Outline(i); pts = [(M(o.CPoint(k).x), M(o.CPoint(k).y)) for k in range(o.PointCount())]
        if len(pts) >= 3: out.append(Polygon(pts).buffer(0))
    return out
def obstacles(L):
    g = []
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.IsOnLayer(L) or p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                sp = pcbnew.SHAPE_POLY_SET(); p.TransformShapeToPolygon(sp, L, 0, mm(0.01))
                for q in poly_of(sp): g.append((q, p.GetNetname() or '~'))
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            g.append((Point(M(t.GetPosition().x), M(t.GetPosition().y)).buffer(M(t.GetWidth()) / 2), t.GetNetname()))
        elif t.GetLayer() == L:
            g.append((LineString([(M(t.GetStart().x), M(t.GetStart().y)), (M(t.GetEnd().x), M(t.GetEnd().y))]).buffer(M(t.GetWidth()) / 2), t.GetNetname()))
    for z in b.Zones():
        if z.GetIsRuleArea():
            if z.IsOnLayer(L):
                for q in poly_of(z.Outline()): g.append((q, '~keepout'))
            continue
        if not z.IsOnLayer(L) or z.GetAssignedPriority() <= 1: continue
        for q in poly_of(z.GetFilledPolysList(L)): g.append((q, z.GetNetname()))
    return g
edge = box(0.5, 0.5, 159.5, 104.5)
total_before = total_after = 0
changed = 0
plan = []
for L in LAYERS:
    added = []
    obs = obstacles(L); tree = STRtree([q for q, n in obs]); nets_of = [n for q, n in obs]
    fixed = set()
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T: fixed.add((t.GetNetname(), K(M(t.GetPosition().x), M(t.GetPosition().y))))
    segs = collections.defaultdict(list)
    for t in b.GetTracks():
        if t.Type() != pcbnew.PCB_VIA_T and t.GetLayer() == L and t.GetLength() > 0:
            segs[t.GetNetname()].append(t)
    for net, ts in segs.items():
        if net in KEEP: continue
        adj = collections.defaultdict(list)
        for t in ts:
            a = K(M(t.GetStart().x), M(t.GetStart().y)); c = K(M(t.GetEnd().x), M(t.GetEnd().y))
            adj[a].append((t, c)); adj[c].append((t, a))
        def is_fixed(n):
            if (net, n) in fixed or len(adj[n]) != 2: return True
            w = {round(M(t.GetWidth()), 3) for t, _ in adj[n]}
            if len(w) > 1: return True
            for f in b.GetFootprints():
                pass
            return False
        padhit = {}
        def on_pad(n):
            if n not in padhit:
                pt = V(*n); padhit[n] = any(p.HitTest(pt) for f in b.GetFootprints() for p in f.Pads() if p.GetNetname() == net)
            return padhit[n]
        seen = set()
        for start in list(adj):
            if not (is_fixed(start) or on_pad(start)): continue
            for t0, nxt in adj[start]:
                if id(t0) in seen: continue
                chain_t, nodes = [t0], [start, nxt]; seen.add(id(t0))
                while not (is_fixed(nodes[-1]) or on_pad(nodes[-1])):
                    cand = [(t, o) for t, o in adj[nodes[-1]] if id(t) not in seen]
                    if not cand: break
                    t, o = cand[0]; seen.add(id(t)); chain_t.append(t); nodes.append(o)
                if len(chain_t) < 3: continue
                w = M(chain_t[0].GetWidth())
                def clear(path):
                    for (x1, y1), (x2, y2) in zip(path, path[1:]):
                        g = LineString([(x1, y1), (x2, y2)]).buffer(w / 2)
                        if not edge.contains(g): return False
                        for i in tree.query(g.buffer(CLR)):
                            if nets_of[i] != net and tree.geometries[i].distance(g) < CLR: return False
                        for q, n in added:
                            if n != net and q.distance(g) < CLR: return False
                    return True
                def options(a, c):
                    (x1, y1), (x2, y2) = a, c; dx, dy = x2 - x1, y2 - y1
                    if abs(abs(dx) - abs(dy)) < 1e-3 or abs(dx) < 1e-3 or abs(dy) < 1e-3: return [[a, c]]
                    d = min(abs(dx), abs(dy)); sx, sy = math.copysign(1, dx), math.copysign(1, dy)
                    m1 = (x1 + sx * d, y1 + sy * d); m2 = (x2 - sx * d, y2 - sy * d)
                    return [[a, m1, c], [a, m2, c], [a, c]]
                length = lambda pts: sum(math.dist(p, q) for p, q in zip(pts, pts[1:]))
                old_len = sum(M(t.GetLength()) for t in chain_t)
                newpath, i = [nodes[0]], 0
                while i < len(nodes) - 1:
                    best = None
                    for j in range(len(nodes) - 1, i + 1, -1):
                        for opt in options(nodes[i], nodes[j]):
                            if clear(opt): best = (j, opt); break
                        if best: break
                    if best:
                        j, opt = best; newpath += opt[1:]; i = j
                    else:
                        newpath.append(nodes[i + 1]); i += 1
                # drop collinear points
                pts = [newpath[0]]
                for p in newpath[1:]:
                    if len(pts) >= 2:
                        (ax, ay), (bx, by) = pts[-2], pts[-1]
                        if abs((bx - ax) * (p[1] - ay) - (by - ay) * (p[0] - ax)) < 1e-4: pts[-1] = p; continue
                    pts.append(p)
                if len(pts) - 1 >= len(chain_t) or length(pts) > old_len + 1e-3: continue
                total_before += len(chain_t); total_after += len(pts) - 1; changed += 1
                plan.append((chain_t, pts, w, L, net))
                for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
                    added.append((LineString([(x1, y1), (x2, y2)]).buffer(w / 2), net))
    print(b.GetLayerName(L), 'done', changed, total_before, '->', total_after, flush=True)
for chain_t, pts, w, L, net in plan:
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(V(x1, y1)); t.SetEnd(V(x2, y2)); t.SetWidth(mm(w)); t.SetLayer(L); t.SetNet(b.FindNet(net)); b.Add(t)
for chain_t, pts, w, L, net in plan:
    for t in chain_t: b.Remove(t)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[2], b)
print('chains', changed, 'segments', total_before, '->', total_after)

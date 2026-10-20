"""Ground island stitching: every filled fragment of a ground net (GND, GNDP, GND_ISO) on F.Cu / In2 / B.Cu that
holds pads of that net but no via of it gets a 0.6/0.3 via to the In1 plane of the same net. The via spot is
searched inside the fragment (shrunk), inside the In1 fill, and clear of every other-net object on all layers,
preferring spots close to the fragment's pads. Repeats with a refill until nothing changes.
usage: islands5.py in.kicad_pcb out.kicad_pcb"""
import math, sys
import pcbnew
from shapely.geometry import Point, Polygon, box, LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree

M, mm = pcbnew.ToMM, pcbnew.FromMM
NETS = ("GND", "GNDP", "GND_ISO")
LAYERS = (pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)
VD, CLR = 0.6, 0.22


def polys(sp):
    out = []
    for i in range(sp.OutlineCount()):
        o = sp.Outline(i)
        pts = [(M(o.CPoint(k).x), M(o.CPoint(k).y)) for k in range(o.PointCount())]
        if len(pts) < 3:
            continue
        hs = []
        for h in range(sp.HoleCount(i)):
            ho = sp.Hole(i, h)
            hs.append([(M(ho.CPoint(k).x), M(ho.CPoint(k).y)) for k in range(ho.PointCount())])
        out.append(Polygon(pts, hs).buffer(0))
    return out


def one_pass(b):
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    # other-net obstacles per layer (all layers matter for a through via)
    obst = []
    for z in b.Zones():
        if z.GetIsRuleArea():
            for q in polys(z.Outline()):
                obst.append((q, "__keepout__"))
            continue
        for L in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
            if z.IsOnLayer(L):
                for q in polys(z.GetFilledPolysList(L)):
                    obst.append((q, z.GetNetname()))
    for t in b.GetTracks():
        s, e = t.GetStart(), t.GetEnd()
        if t.Type() == pcbnew.PCB_VIA_T:
            g = Point(M(s.x), M(s.y)).buffer(M(t.GetWidth()) / 2)
        else:
            g = LineString([(M(s.x), M(s.y)), (M(e.x), M(e.y))]).buffer(M(t.GetWidth()) / 2)
        obst.append((g, t.GetNetname()))
    pads = []
    for f in b.GetFootprints():
        for p in f.Pads():
            bb = p.GetBoundingBox()
            g = box(M(bb.GetX()), M(bb.GetY()), M(bb.GetRight()), M(bb.GetBottom()))
            th = p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH)
            obst.append((g.buffer(0.08) if th else g, p.GetNetname() if not th else "__hole__" + p.GetNetname()))
            pads.append((g, p.GetNetname(), th, p))
    tree = STRtree([o[0] for o in obst])
    lay_obst = {L: [] for L in LAYERS}
    for z in b.Zones():
        if not z.GetIsRuleArea():
            for L in LAYERS:
                if z.IsOnLayer(L):
                    lay_obst[L] += [(q, z.GetNetname()) for q in polys(z.GetFilledPolysList(L))]
    for t in b.GetTracks():
        s_, e_ = t.GetStart(), t.GetEnd()
        if t.Type() == pcbnew.PCB_VIA_T:
            for L in LAYERS:
                lay_obst[L].append((Point(M(s_.x), M(s_.y)).buffer(M(t.GetWidth()) / 2), t.GetNetname()))
        elif t.GetLayer() in LAYERS:
            lay_obst[t.GetLayer()].append((LineString([(M(s_.x), M(s_.y)), (M(e_.x), M(e_.y))]).buffer(M(t.GetWidth()) / 2), t.GetNetname()))
    for g, n, th, p in pads:
        for L in LAYERS:
            if th or p.IsOnLayer(L):
                lay_obst[L].append((g, n))
    lay_tree = {L: STRtree([o[0] for o in lay_obst[L]]) for L in LAYERS}
    vias = {n: [Point(M(t.GetPosition().x), M(t.GetPosition().y)) for t in b.GetTracks()
                if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == n] for n in NETS}
    edge = box(0.8, 0.8, 159.2, 104.2)
    added = []
    for net in NETS:
        plane = unary_union([q for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() == net
                             and z.IsOnLayer(pcbnew.In1_Cu) for q in polys(z.GetFilledPolysList(pcbnew.In1_Cu))])
        if plane.is_empty:
            continue
        plane_core = plane.buffer(-(VD / 2 + 0.05))
        for L in LAYERS:
            frags = [q for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() == net and z.IsOnLayer(L)
                     for q in polys(z.GetFilledPolysList(L))]
            # each zone's fragments on their own: overlapping same-net zones are not trusted to be joined
            for fr in frags:
                mine = [g for g, n, th, p in pads if n == net and (th or p.IsOnLayer(L)) and g.intersects(fr)]
                if not mine:
                    continue
                if any(fr.buffer(0.01).contains(v) for v in vias[net] + added_pts(added, net)):
                    continue
                if any(th for g, n, th, p in pads if n == net and th and g.intersects(fr)):
                    continue                          # a through-hole pad of the net already ties the layers
                core = fr.buffer(-(VD / 2)).intersection(plane_core).intersection(edge)
                if core.is_empty:
                    if escape(b, net, L, fr, plane_core, obst, tree, lay_obst[L], lay_tree[L], added):
                        continue
                    print(f"  no room: {net} L{L} at {fr.representative_point().coords[0]} area {fr.area:.2f}")
                    continue
                target = unary_union(mine).centroid
                best = None
                x0, y0, x1, y1 = core.bounds
                step = max(0.1, min(0.5, fr.area ** 0.5 / 40))
                ys = [y0 + i * step for i in range(int((y1 - y0) / step) + 1)]
                xs = [x0 + i * step for i in range(int((x1 - x0) / step) + 1)]
                for y in ys:
                    for x in xs:
                        pt = Point(x, y)
                        if not core.contains(pt):
                            continue
                        d = pt.distance(target)
                        if best and d >= best[0]:
                            continue
                        c = pt.buffer(VD / 2 + CLR)
                        bad = False
                        for k in tree.query(c):
                            g, n = obst[k]
                            if n == net and g.geom_type != "Polygon":
                                continue
                            if n == net:
                                # own-net copper is fine, except SMD pads (no via-in-pad) and holes
                                if g.intersects(pt.buffer(VD / 2)) and any(g is pg and not th for pg, nn, th, p in pads):
                                    bad = True
                                    break
                                continue
                            if g.intersects(c):
                                bad = True
                                break
                        if not bad:
                            best = (d, pt)
                if best is None and escape(b, net, L, fr, plane_core, obst, tree, lay_obst[L], lay_tree[L], added):
                    continue
                if best is None:
                    print(f"  blocked: {net} L{L} at {fr.representative_point().coords[0]} area {fr.area:.2f}")
                    continue
                pt = best[1]
                v = pcbnew.PCB_VIA(b)
                v.SetPosition(pcbnew.VECTOR2I(mm(round(pt.x, 3)), mm(round(pt.y, 3))))
                v.SetWidth(mm(VD)); v.SetDrill(mm(0.3)); v.SetNet(b.FindNet(net))
                b.Add(v)
                added.append((net, pt))
                obst.append((pt.buffer(VD / 2), net))
                print(f"  via {net} L{L} ({pt.x:.2f},{pt.y:.2f}) frag area {fr.area:.2f}")
    return len(added)


def via_ok(pt, net, obst, tree):
    c = pt.buffer(VD / 2 + CLR)
    for k in tree.query(c):
        g, n = obst[k]
        if n == net:
            continue
        if g.intersects(c):
            return False
    return True


def escape(b, net, L, fr, plane_core, obst, tree, lobst, ltree, added):
    """fragment with no legal via spot inside: 0.25 mm track from inside the fragment to a via outside it"""
    TW = 0.25
    inner = fr.buffer(-0.15)
    if inner.is_empty:
        inner = fr
    x0, y0, x1, y1 = inner.bounds
    starts = [Point(x0 + i * 0.25, y0 + j * 0.25) for i in range(int((x1 - x0) / 0.25) + 1)
              for j in range(int((y1 - y0) / 0.25) + 1)]
    starts = [p for p in starts if inner.contains(p)] or [inner.representative_point()]
    best = None
    for st in starts:
        for r10 in range(6, 36, 2):
            r = r10 / 10
            if best and r >= best[0]:
                break
            for k in range(48):
                a = 2 * math.pi * k / 48
                pt = Point(st.x + r * math.cos(a), st.y + r * math.sin(a))
                if not plane_core.contains(pt) or not box(0.8, 0.8, 159.2, 104.2).contains(pt):
                    continue
                if not via_ok(pt, net, obst, tree):
                    continue
                tr = LineString([(st.x, st.y), (pt.x, pt.y)]).buffer(TW / 2 + CLR)
                if any(lobst[i][1] != net and lobst[i][0].intersects(tr) for i in ltree.query(tr)):
                    continue
                best = (r, st, pt)
                break
    if best is None:
        return False
    _, st, pt = best
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(mm(round(pt.x, 3)), mm(round(pt.y, 3))))
    v.SetWidth(mm(VD)); v.SetDrill(mm(0.3)); v.SetNet(b.FindNet(net)); b.Add(v)
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(mm(round(st.x, 3)), mm(round(st.y, 3)))); t.SetEnd(v.GetPosition())
    t.SetWidth(mm(TW)); t.SetLayer(L); t.SetNet(b.FindNet(net)); b.Add(t)
    added.append((net, pt))
    obst.append((pt.buffer(VD / 2), net))
    print(f"  escape {net} L{L} ({st.x:.2f},{st.y:.2f}) -> via ({pt.x:.2f},{pt.y:.2f})")
    return True


def added_pts(added, net):
    return [p for n, p in added if n == net]


def main(src, dst):
    b = pcbnew.LoadBoard(src)
    tot = 0
    for _ in range(4):
        n = one_pass(b)
        tot += n
        if n == 0:
            break
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(dst, b)
    print("island vias added", tot)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

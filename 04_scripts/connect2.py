"""Close remaining unconnected items with exact-geometry checked short routes (shapely).
Candidates: straight / L / Z on F.Cu, B.Cu, In2.Cu, optionally with an escape via at each end.
Usage: connect.py in out"""
import itertools, math, sys
import pcbnew
from shapely.geometry import LineString, Point, box
from shapely.strtree import STRtree

sys.path.insert(0, "/home/claude/dcdc")
from fix_unconnected import drc
import gen_pcb3 as GP

mm, MM = pcbnew.FromMM, pcbnew.ToMM
F, B, I2, I1 = pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In2_Cu, pcbnew.In1_Cu
TW, CLR, VD, VDR = 0.15, 0.2, 0.6, 0.3
LAYERS = (F, B, I2)


def geoms(b):
    """per-layer list of (geom, net) for all copper except zones on F/B/In2 (zones are re-filled later)."""
    per = {L: [] for L in LAYERS + (I1,)}
    for fp in b.GetFootprints():
        for pd in fp.Pads():
            bb = pd.GetBoundingBox()
            x0, y0, x1, y1 = MM(bb.GetX()), MM(bb.GetY()), MM(bb.GetRight()), MM(bb.GetBottom())
            g = Point((x0 + x1) / 2, (y0 + y1) / 2).buffer((x1 - x0) / 2) if pd.GetShape() == pcbnew.PAD_SHAPE_CIRCLE else box(x0, y0, x1, y1)
            th = pd.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH)
            for L in per:
                if th or pd.IsOnLayer(L):
                    per[L].append((g, pd.GetNetname() if pd.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH else "~hole"))
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            g = Point(MM(t.GetPosition().x), MM(t.GetPosition().y)).buffer(MM(t.GetWidth()) / 2)
            for L in per:
                per[L].append((g, t.GetNetname()))
        else:
            g = LineString([(MM(t.GetStart().x), MM(t.GetStart().y)), (MM(t.GetEnd().x), MM(t.GetEnd().y))]).buffer(MM(t.GetWidth()) / 2)
            if t.GetLayer() in per:
                per[t.GetLayer()].append((g, t.GetNetname()))
    return per


def main(src, dst):
    b = pcbnew.LoadBoard(src)
    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())
    base, unc = drc(b)
    print("start", base, len(unc))
    keep = [box(GP.XB - GP.BAND, 0, GP.XB + GP.BAND, GP.H), box(GP.XC - GP.BAND, GP.YC - GP.BAND, GP.XC + GP.BAND, GP.H),
            box(GP.XC - GP.BAND, GP.YC - GP.BAND, GP.W, GP.YC + GP.BAND)]
    edge = box(0.6, 0.6, GP.W - 0.6, GP.H - 0.6)
    for (a, c, net, ta, tc) in unc:
        per = geoms(b)
        trees = {L: (STRtree([g for g, n in per[L]]), [n for g, n in per[L]]) for L in per}

        def ok(g, L):
            if not edge.contains(g) or any(g.intersects(k) for k in keep):
                return False
            tree, nets = trees[L]
            for i in tree.query(g.buffer(CLR)):
                if nets[i] != net and tree.geometries[i].distance(g) < CLR:
                    return False
            return True

        def via_ok(p):
            g = Point(p).buffer(VD / 2)
            return all(ok(g, L) for L in (F, B, I2, I1)) if not any(
                nets_ == net for nets_ in []) else True

        found = None
        cands = []
        (ax, ay), (cx, cy) = a, c
        mids = [0.0, 0.5, -0.5, 1.0, -1.0, 1.5, -1.5, 2.5, -2.5]
        for L in LAYERS:
            for path in ([(a, c)], [(a, (cx, ay)), ((cx, ay), c)], [(a, (ax, cy)), ((ax, cy), c)]):
                cands.append((L, path, []))
            for d in mids:
                mx, my = (ax + cx) / 2 + d, (ay + cy) / 2 + d
                cands.append((L, [(a, (mx, ay)), ((mx, ay), (mx, cy)), ((mx, cy), c)], []))
                cands.append((L, [(a, (ax, my)), ((ax, my), (cx, my)), ((cx, my), c)], []))
        # with escape vias: short F.Cu stubs to vias near both ends, then inner/bottom route
        stubs = [(0.0, 0.0)]
        for r in (0.8, 1.0, 1.2, 1.4, 1.6, 1.9, 2.2, 2.6):
            for k in range(24):
                th = 2 * math.pi * k / 24
                stubs.append((round(r * math.cos(th), 3), round(r * math.sin(th), 3)))
        for L in (B, I2):
            for (dxa, dya), (dxc, dyc) in itertools.islice(itertools.product(stubs, stubs), 0, 40000):
                va, vc = (ax + dxa, ay + dya), (cx + dxc, cy + dyc)
                fs = [s_ for s_ in ((a, va), (c, vc)) if s_[0] != s_[1]]
                if (dxa, dya) == (0.0, 0.0) and ta == "Pad" or (dxc, dyc) == (0.0, 0.0) and tc == "Pad":
                    continue
                cands.append((L, [(va, (vc[0], va[1])), ((vc[0], va[1]), vc)], fs))
                cands.append((L, [(va, (va[0], vc[1])), ((va[0], vc[1]), vc)], fs))
                cands.append((L, [(va, vc)], fs))
        for L, path, fst in cands:
            segs = [s for s in path if s[0] != s[1]]
            if not segs:
                continue
            if fst:
                if not all(ok(LineString(s).buffer(TW / 2), F) for s in fst):
                    continue
                if not all(ok(Point(s[1]).buffer(VD / 2), LL) for s in fst for LL in (F, B, I2, I1)):
                    continue
            if all(ok(LineString(s).buffer(TW / 2), L) for s in segs):
                found = (L, segs, fst)
                break
        if not found:
            print("FAIL", net, a, c)
            continue
        L, segs, fst = found
        ni = b.FindNet(net)
        items = []
        for (p, q), lay in [(s, L) for s in segs] + [(s, F) for s in fst]:
            t = pcbnew.PCB_TRACK(b)
            t.SetStart(pcbnew.VECTOR2I(mm(p[0]), mm(p[1]))); t.SetEnd(pcbnew.VECTOR2I(mm(q[0]), mm(q[1])))
            t.SetWidth(mm(TW)); t.SetLayer(lay); t.SetNet(ni); b.Add(t); items.append(t)
        for s in fst:
            v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(mm(s[1][0]), mm(s[1][1])))
            v.SetWidth(mm(VD)); v.SetDrill(mm(VDR)); v.SetNet(ni); v.SetLayerPair(F, B); b.Add(v); items.append(v)
        filler.Fill(b.Zones())
        bad, _ = drc(b)
        if bad > base:
            import re as _re
            t_ = open("/tmp/fix_drc.rpt").read()
            for blk in _re.split(r"\n(?=\[)", t_):
                if net in blk and not blk.startswith("[unconnected"):
                    print("   ", blk[:300].replace("\n", " | "))
            print("DRC REJECT", net, a, c, bad)
            for it in items:
                b.Remove(it)
        else:
            print("routed", net, a, "->", c, b.GetLayerName(L), "vias" if fst else "")
    filler.Fill(b.Zones())
    base, unc = drc(b)
    print("end: violations", base, "unconnected", len(unc))
    pcbnew.SaveBoard(dst, b)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

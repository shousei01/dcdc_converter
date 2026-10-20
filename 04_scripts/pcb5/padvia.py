"""Ground pads that no ground fill reaches (fine-pitch pins, pads boxed in by other nets): a short F.Cu track
(0.25 mm) from the pad to a new 0.6/0.3 via that lands on the In1 plane of the same net. Candidate via spots on
rings around the pad, checked against all other-net copper on every layer; the shortest legal one wins.
usage: padvia.py in.kicad_pcb drc_report out.kicad_pcb"""
import math, re, sys
import pcbnew
from shapely.geometry import Point, LineString, box
from shapely.ops import unary_union
from shapely.strtree import STRtree
sys.path.insert(0, "/home/claude/dcdc/pcb5")
from islands5 import polys

M, mm = pcbnew.ToMM, pcbnew.FromMM
GNDS = ("GND", "GNDP", "GND_ISO")
VD, TW, CLR = 0.6, 0.25, 0.21


def main(src, rpt, dst):
    b = pcbnew.LoadBoard(src)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    want = set()
    for blk in re.split(r"\n(?=\[)", open(rpt).read()):
        if blk.startswith("[unconnected_items]"):
            for ref, num in re.findall(r"Pad (\S+) \[(?:GND|GNDP|GND_ISO)\] of (\S+)", blk):
                want.add((num, ref))
    obstF, obstA = [], []                     # (geom, net): F.Cu only / any layer (via)
    for z in b.Zones():
        if z.GetIsRuleArea():
            for q in polys(z.Outline()):
                obstA.append((q, "__keep__")); obstF.append((q, "__keep__"))
            continue
        for L in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
            if z.IsOnLayer(L):
                for q in polys(z.GetFilledPolysList(L)):
                    obstA.append((q, z.GetNetname()))
                    if L == pcbnew.F_Cu:
                        obstF.append((q, z.GetNetname()))
    for t in b.GetTracks():
        s, e = t.GetStart(), t.GetEnd()
        if t.Type() == pcbnew.PCB_VIA_T:
            g = Point(M(s.x), M(s.y)).buffer(M(t.GetWidth()) / 2)
            obstA.append((g, t.GetNetname())); obstF.append((g, t.GetNetname()))
        else:
            g = LineString([(M(s.x), M(s.y)), (M(e.x), M(e.y))]).buffer(M(t.GetWidth()) / 2)
            obstA.append((g, t.GetNetname()))
            if t.GetLayer() == pcbnew.F_Cu:
                obstF.append((g, t.GetNetname()))
    targets = []
    for f in b.GetFootprints():
        for p in f.Pads():
            bb = p.GetBoundingBox()
            g = box(M(bb.GetX()), M(bb.GetY()), M(bb.GetRight()), M(bb.GetBottom()))
            th = p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH)
            n = p.GetNetname()
            obstA.append((g.buffer(0.08) if th else g, "__pad__" + n))
            if p.IsOnLayer(pcbnew.F_Cu):
                obstF.append((g, n))
            if (f.GetReference(), p.GetNumber()) in want:
                targets.append((f.GetReference(), p.GetNumber(), n, g, p))
    tA = STRtree([o[0] for o in obstA]); tF = STRtree([o[0] for o in obstF])
    planes = {n: unary_union([q for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() == n
                              and z.IsOnLayer(pcbnew.In1_Cu) for q in polys(z.GetFilledPolysList(pcbnew.In1_Cu))])
              for n in GNDS}
    for ref, num, net, g, p in targets:
        c = g.centroid
        best = None
        for r10 in range(7, 30):
            r = r10 / 10
            for k in range(36):
                a = 2 * math.pi * k / 36
                pt = Point(c.x + r * math.cos(a), c.y + r * math.sin(a))
                if not planes[net].buffer(-(VD / 2 + 0.05)).contains(pt):
                    continue
                vg = pt.buffer(VD / 2 + CLR)
                if any(obstA[i][1] != net and obstA[i][0].intersects(vg) for i in tA.query(vg)):
                    continue
                tr = LineString([(c.x, c.y), (pt.x, pt.y)]).buffer(TW / 2 + CLR)
                if any(obstF[i][1] != net and obstF[i][0].intersects(tr) for i in tF.query(tr)):
                    continue
                best = pt
                break
            if best:
                break
        if best is None:
            print("  no spot for", ref, num, net, c.coords[0]); continue
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(pcbnew.VECTOR2I(mm(round(best.x, 3)), mm(round(best.y, 3))))
        v.SetWidth(mm(VD)); v.SetDrill(mm(0.3)); v.SetNet(b.FindNet(net)); b.Add(v)
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(pcbnew.VECTOR2I(mm(c.x), mm(c.y))); t.SetEnd(v.GetPosition())
        t.SetWidth(mm(TW)); t.SetLayer(pcbnew.F_Cu); t.SetNet(b.FindNet(net)); b.Add(t)
        obstA.append((best.buffer(VD / 2), net)); obstF.append((best.buffer(VD / 2), net))
        tA = STRtree([o[0] for o in obstA]); tF = STRtree([o[0] for o in obstF])
        print(f"  {ref}.{num} {net}: via ({best.x:.2f},{best.y:.2f})")
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(dst, b)


if __name__ == "__main__":
    main(*sys.argv[1:4])

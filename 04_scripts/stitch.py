"""Ground stitching: a via on a ~5 mm grid wherever the same ground net is poured on F, In1, In2 and B
(GND, GNDP, GND_ISO each in its own domain), clear of other copper, >= 2 mm from the nearest via. usage: stitch.py in out"""
import sys, pcbnew
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree
mm, M = pcbnew.FromMM, pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1]); pcbnew.ZONE_FILLER(b).Fill(b.Zones())
LAY = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
def polys(sp):
    out = []
    for i in range(sp.OutlineCount()):
        o = sp.Outline(i); pts = [(M(o.CPoint(k).x), M(o.CPoint(k).y)) for k in range(o.PointCount())]
        if len(pts) >= 3: out.append(Polygon(pts).buffer(0))
    return out
vias = [Point(M(t.GetPosition().x), M(t.GetPosition().y)) for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
holes = []
for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
            r = p.GetBoundingBox(); holes.append(Point(M(r.Centre().x), M(r.Centre().y)).buffer(M(max(r.GetWidth(), r.GetHeight())) / 2))
keep = [q for z in b.Zones() if z.GetIsRuleArea() for q in polys(z.Outline())]
added = 0
for net in ('GND', 'GNDP', 'GND_ISO'):
    cover = None
    for L in LAY:
        u = unary_union([q for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() == net and z.IsOnLayer(L) for q in polys(z.GetFilledPolysList(L))])
        cover = u if cover is None else cover.intersection(u)
    if cover is None or cover.is_empty: continue
    x0, y0, x1, y1 = cover.bounds
    pts = []
    y = y0 + 2.0
    while y < y1:
        x = x0 + 2.0
        while x < x1:
            p = Point(x, y)
            if cover.contains(p.buffer(0.3 + 0.35)) and all(p.distance(v) > 2.0 for v in vias) \
               and all(p.distance(h) > 1.2 for h in holes) and not any(k.distance(p) < 1.0 for k in keep):
                pts.append((x, y)); vias.append(p)
            x += 5.0
        y += 5.0
    for x, y in pts:
        v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y))); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3))
        v.SetNet(b.FindNet(net)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); b.Add(v)
    print(net, len(pts)); added += len(pts)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[2], b)
print('stitching vias', added)

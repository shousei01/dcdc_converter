"""list routed tracks/vias that cut through power pours of other nets (zone outlines) on the same layer"""
import sys, pcbnew
from shapely.geometry import LineString, Point, Polygon
MM = pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
Z = []
for z in b.Zones():
    if z.GetIsRuleArea() or z.GetZoneName().startswith("FLOOD"): continue
    o = z.Outline().Outline(0)
    poly = Polygon([(MM(o.CPoint(k).x), MM(o.CPoint(k).y)) for k in range(o.PointCount())]).buffer(0)
    for L in (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu):
        if z.IsOnLayer(L): Z.append((z.GetNetname(), L, poly))
n = 0
for t in b.GetTracks():
    net = t.GetNetname()
    s, e = t.GetStart(), t.GetEnd()
    if t.Type() == pcbnew.PCB_VIA_T:
        g = Point(MM(s.x), MM(s.y)).buffer(MM(t.GetWidth()) / 2); layers = [pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu]
    else:
        g = LineString([(MM(s.x), MM(s.y)), (MM(e.x), MM(e.y))]).buffer(MM(t.GetWidth()) / 2); layers = [t.GetLayer()]
    for zn, L, poly in Z:
        if zn != net and L in layers and g.intersects(poly):
            a = g.intersection(poly).area
            if a > 0.01:
                n += 1
                print(f"{'via' if t.Type()==pcbnew.PCB_VIA_T else 'trk'} {net:12s} L{L:2d} x {zn:8s} at ({MM(s.x):.1f},{MM(s.y):.1f})-({MM(e.x):.1f},{MM(e.y):.1f}) area {a:.2f}")
print("total", n)

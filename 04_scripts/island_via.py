import sys,pcbnew;from shapely.geometry import Polygon
M=pcbnew.ToMM;mm=pcbnew.FromMM
b=pcbnew.LoadBoard(sys.argv[1]);net=b.FindNet('GNDP')
for z in b.Zones():
    if z.GetZoneName()!='FLOOD_GNDP' or not z.IsOnLayer(pcbnew.F_Cu): continue
    fp=z.GetFilledPolysList(pcbnew.F_Cu)
    for i in range(fp.OutlineCount()):
        a=fp.Outline(i).Area()/1e12
        if a>100 or a<1: continue
        o=fp.Outline(i)
        if M(o.BBox().Centre())[0]<40: continue
        hs=[fp.Hole(i,h) for h in range(fp.HoleCount(i))]
        P=Polygon([M(o.CPoint(k)) for k in range(o.PointCount())],[[M(h.CPoint(k)) for k in range(h.PointCount())] for h in hs])
        core=P.buffer(-0.32)
        if core.is_empty: print('no room',P.centroid); continue
        c=core.representative_point() if not core.contains(core.centroid) else core.centroid
        print('via',round(c.x,2),round(c.y,2),a)
        if '--go' in sys.argv:
            v=pcbnew.PCB_VIA(b);v.SetPosition(pcbnew.VECTOR2I(mm(c.x),mm(c.y)));v.SetWidth(mm(0.6));v.SetDrill(mm(0.3));v.SetNet(net);b.Add(v)
if '--go' in sys.argv:
    f=pcbnew.ZONE_FILLER(b);f.Fill(b.Zones());b.Save(sys.argv[2])

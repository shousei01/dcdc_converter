import pcbnew,sys,re
mm,M=pcbnew.FromMM,pcbnew.ToMM
b=pcbnew.LoadBoard(sys.argv[1])
keep={(77.22,59.6,76.15,58.52),(80.49,59.6,77.22,59.6),(80.5,59.6,81.15,58.95)}
rm=[]
for t in b.GetTracks():
    if t.GetNetname()=="EN_AUX" and t.GetClass()=="PCB_TRACK":
        k=tuple(round(M(v),2) for v in (t.GetStart().x,t.GetStart().y,t.GetEnd().x,t.GetEnd().y))
        if k not in keep: rm.append(t)
for t in rm: b.Remove(t)
net=b.FindNet("EN_AUX")
def seg(L,pts,w=0.25):
    for (x1,y1),(x2,y2) in zip(pts,pts[1:]):
        t=pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
        t.SetWidth(mm(w)); t.SetLayer(L); t.SetNet(net); b.Add(t)
seg(pcbnew.F_Cu,[(82.53,54.66),(82.1,54.85)])
seg(pcbnew.F_Cu,[(81.1375,58.95),(81.4,59.45)])
seg(pcbnew.B_Cu,[(82.1,54.85),(82.1,55.65),(81.8,55.95),(81.8,58.2),(81.7,58.35),(81.4,58.65),(81.4,59.45)],0.2)
b.Save(sys.argv[2])
b=pcbnew.LoadBoard(sys.argv[2]); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(sys.argv[2])
pcbnew.WriteDRCReport(b,'s.rpt',pcbnew.EDA_UNITS_MILLIMETRES,True)
t=open('s.rpt').read(); print(re.findall(r'\*\* Found .*',t))
for blk in re.split(r'\n(?=\[)',t):
    if blk.startswith('[') and 'lib_footprint' not in blk: print(blk[:300])

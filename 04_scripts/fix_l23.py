import pcbnew,sys,re
sys.path.insert(0,'/home/claude/dcdc')
import maze
from fix_unconnected import drc
mm,M=pcbnew.FromMM,pcbnew.ToMM
b=pcbnew.LoadBoard(sys.argv[1])
def seg(net,x1,y1,x2,y2,w,layer=pcbnew.F_Cu):
    t=pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNet(b.FindNet(net)); b.Add(t)
def near(a,b_,tol=0.01): return abs(a-b_)<tol
# 1) EN_AUX: remove the detour through L2 and reroute
rm=[]
for t in b.GetTracks():
    if t.GetNetname()=="EN_AUX" and t.GetClass()=="PCB_TRACK":
        xs=[M(t.GetStart().x),M(t.GetEnd().x)]; ys=[M(t.GetStart().y),M(t.GetEnd().y)]
        if max(xs)>81.0 and min(ys)>54 and max(ys)<60: rm.append(t)
for t in rm: b.Remove(t)
print("EN_AUX removed",len(rm))
# 2) VIN under L3: drop the two diagonals + horizontal, run down past pad bottom
kill=[(29.806,69.124,28.973,69.957),(28.973,69.957,23.122,69.957),(23.122,69.957,22.64,69.475),(30.51,71.493,28.973,69.957),(31.05,71.493,30.51,71.493)]
rmv=[]
for t in b.GetTracks():
    if t.GetNetname()!="VIN" or t.GetClass()!="PCB_TRACK": continue
    s=(M(t.GetStart().x),M(t.GetStart().y),M(t.GetEnd().x),M(t.GetEnd().y))
    if any(all(near(s[i],k[i]) for i in range(4)) or all(near(s[i],k[j]) for i,j in zip(range(4),(2,3,0,1))) for k in kill): rmv.append(t)
print("VIN removed",len(rmv))
for t in rmv: b.Remove(t)
Y=71.493
seg("VIN",29.806,69.124,29.806,Y,1.5)
seg("VIN",29.806,Y,31.05,Y,1.5)
seg("VIN",29.806,Y,24.6,Y,1.5)
seg("VIN",24.6,Y,22.64,69.533,1.5)
b.Save('/tmp/claude-0/dr/stage.kicad_pcb')
b=pcbnew.LoadBoard('/tmp/claude-0/dr/stage.kicad_pcb')
f=pcbnew.ZONE_FILLER(b); f.Fill(b.Zones())
bad,unc=drc(b); print("bad",bad,"unc",[(u[2]) for u in unc])
for (a,c,net,ta,tc) in unc[:1]:
    lab=maze.raster(b)
    la,lc=maze.layer_at(b,a,ta),maze.layer_at(b,c,tc)
    p=maze.route(lab,b.FindNet(net).GetNetCode(),a,la,c,lc)
    print(net,a,c,"path",bool(p))
    if p: maze.emit(b,p,b.FindNet(net))
b.BuildConnectivity(); f.Fill(b.Zones())
b.Save(sys.argv[2])

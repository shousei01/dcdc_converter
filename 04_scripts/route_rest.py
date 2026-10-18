import pcbnew,sys
sys.path.insert(0,'/home/claude/dcdc')
import maze
from fix_unconnected import drc
src,dst=sys.argv[1],sys.argv[2]
for it in range(4):
    b=pcbnew.LoadBoard(src); f=pcbnew.ZONE_FILLER(b); f.Fill(b.Zones())
    bad,unc=drc(b); print("iter",it,"bad",bad,"unc",[(u[2],u[0],u[1]) for u in unc])
    if not unc: b.Save(dst); break
    a,c,net,ta,tc=unc[0]
    lab=maze.raster(b); p=maze.route(lab,b.FindNet(net).GetNetCode(),a,maze.layer_at(b,a,ta),c,maze.layer_at(b,c,tc))
    print(" route",net,bool(p))
    if not p: break
    maze.emit(b,p,b.FindNet(net)); b.Save('/tmp/claude-0/dr/stage2.kicad_pcb'); src='/tmp/claude-0/dr/stage2.kicad_pcb'

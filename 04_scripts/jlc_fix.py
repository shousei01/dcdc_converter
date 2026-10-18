"""JLCPCB capability fixes: PTH-to-track >= 0.28 mm, silk text stroke >= 0.15 mm.
- J3/J4/J5 THT pads: remove unconnected inner-layer annular rings (In2 tracks between header pins)
- ADDR_H3 F.Cu run under J5.5/J5.6 moved 0.25 mm further from the pads
- every silkscreen text stroke raised to >= 0.15 mm"""
import sys,pcbnew;M=pcbnew.ToMM;mm=pcbnew.FromMM;V=pcbnew.VECTOR2I
def stage1(src,dst):
    global b,n
    b=pcbnew.LoadBoard(src)
    for r in ('J3','J4','J5'):
        for p in b.FindFootprintByReference(r).Pads():
            p.SetRemoveUnconnected(True); p.SetKeepTopBottom(True)
    for t in b.GetTracks():
        if t.GetNetname()=='ADDR_H3' and t.GetLayer()==pcbnew.F_Cu and t.GetClass()=='PCB_TRACK':
            s,e=M(t.GetStart()),M(t.GetEnd())
            if abs(s[1]-102.226)<1e-3: t.SetStart(V(mm(s[0]+(0.25 if s[0]<92 else -0.25)),mm(102.476)))
            if abs(e[1]-102.226)<1e-3: t.SetEnd(V(mm(e[0]+(0.25 if e[0]<92 else -0.25)),mm(102.476)))
    n=0
    def thick(t):
        global n
        if t.GetLayer() in (pcbnew.F_SilkS,pcbnew.B_SilkS) and M(t.GetTextThickness())<0.15: t.SetTextThickness(mm(0.15)); n+=1
    for f in b.GetFootprints():
        thick(f.Reference()); thick(f.Value())
        for x in f.GraphicalItems():
            if x.GetClass() in ('FP_TEXT','PCB_TEXT'): thick(x)
    for d in b.GetDrawings():
        if d.GetClass()=='PCB_TEXT': thick(d)
    print('silk texts thickened',n)
    b.BuildConnectivity(); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(dst)

def stage2(src,dst):
    """J3/J4 CAN In2 runs narrowed to 0.4 mm next to the header pins; ADDR_H2 In2 detour moved clear of J5.4/J5.5."""
    b=pcbnew.LoadBoard(src); ni=b.FindNet('ADDR_H2')
    for t in list(b.GetTracks()):
        if t.GetLayer()!=pcbnew.In2_Cu or t.GetClass()!='PCB_TRACK': continue
        n=t.GetNetname(); s,e=M(t.GetStart()),M(t.GetEnd())
        if n in ('CANH','CANL') and min(s[0],e[0])>153 and max(s[0],e[0])<158.5 and min(s[1],e[1])<96: t.SetWidth(mm(0.4))
        if n=='ADDR_H2' and max(s[1],e[1])>101.3 and min(s[0],e[0])>85 : b.Remove(t)
    for a,c in (((85.08,101.0),(86.53,102.45)),((86.53,102.45),(91.43,102.45)),((91.43,102.45),(91.43,99.75))):
        t=pcbnew.PCB_TRACK(b);t.SetStart(V(mm(a[0]),mm(a[1])));t.SetEnd(V(mm(c[0]),mm(c[1])));t.SetWidth(mm(0.25));t.SetLayer(pcbnew.In2_Cu);t.SetNet(ni);b.Add(t)
    b.BuildConnectivity(); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(dst)

if __name__=="__main__":
    stage1(sys.argv[1],"/tmp/claude-0/jlc_s1.kicad_pcb"); stage2("/tmp/claude-0/jlc_s1.kicad_pcb",sys.argv[2])

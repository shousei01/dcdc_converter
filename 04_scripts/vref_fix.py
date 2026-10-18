"""Hand-route U1 pins 28 (VREF_ADC) and 29 (+3V3A, VDDA) side by side between the R98 and R97 rows."""
import sys,pcbnew;M=pcbnew.ToMM;mm=pcbnew.FromMM;V=pcbnew.VECTOR2I
b=pcbnew.LoadBoard(sys.argv[1])
kill=[]
for t in b.GetTracks():
    if t.GetNetname()!='VREF_ADC': continue
    s,e=M(t.GetStart()),M(t.GetEnd())
    inbox=lambda p:118.6<=p[0]<=124.7 and 76.8<=p[1]<=82.5
    if t.GetClass()=='PCB_VIA' and abs(s[0]-124.6)<.01 and abs(s[1]-76.9)<.01: kill.append(t)
    elif t.GetLayer()==pcbnew.F_Cu and t.GetClass()!='PCB_VIA' and (inbox(s) and inbox(e) or (abs(s[0]-125)<.01 and abs(s[1]-82.4)<.01 and inbox(e))): kill.append(t)
    elif t.GetLayer()==pcbnew.In2_Cu and abs(e[0]-124.6)<.01 and abs(e[1]-76.9)<.01: kill.append(t)
for t in kill: b.Remove(t)
def tr(n,pts,w=0.15):
    ni=b.FindNet(n)
    for a,c in zip(pts,pts[1:]):
        t=pcbnew.PCB_TRACK(b);t.SetStart(V(mm(a[0]),mm(a[1])));t.SetEnd(V(mm(c[0]),mm(c[1])));t.SetWidth(mm(w));t.SetLayer(pcbnew.F_Cu);t.SetNet(ni);b.Add(t)
tr('+3V3A',[(118.67,78.75),(119.55,78.75),(119.77,78.97),(124.4,78.97),(125.0,78.37),(125.17,78.2)])
tr('VREF_ADC',[(118.67,79.25),(119.55,79.25),(119.83,79.53),(124.0,79.53),(124.0,82.4),(125.0,82.4)])
print('removed',len(kill))
pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.Save(sys.argv[2])

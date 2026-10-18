import sys,pcbnew;M=pcbnew.ToMM;mm=pcbnew.FromMM
b=pcbnew.LoadBoard(sys.argv[1])
fp=b.FindFootprintByReference('R106')
olds=[M(p.GetPosition()) for p in fp.Pads()]
kill=[]
for t in b.GetTracks():
    n=t.GetNetname();s,e=M(t.GetStart()),M(t.GetEnd())
    if n=='RST_P': kill.append(t)
    elif n=='VIN_PWM' and (abs(s[0]-114.85)<.01 and abs(s[1]-89.75)<.01 or abs(e[0]-114.85)<.01 and abs(e[1]-89.75)<.01): kill.append(t)
    elif n=='+5V_P' and any(abs(p[0]-q[0])<.05 and abs(p[1]-q[1])<.05 for p in (s,e) for q in olds): kill.append(t); print('5v',s,e,t.GetLayerName())
fp.SetPosition(pcbnew.VECTOR2I(mm(56.1),mm(92.0)))
for t in kill: b.Remove(t)
f=pcbnew.ZONE_FILLER(b);f.Fill(b.Zones());b.Save(sys.argv[2])

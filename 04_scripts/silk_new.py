import sys,pcbnew
a=pcbnew.LoadBoard(sys.argv[1]);b=pcbnew.LoadBoard(sys.argv[2])
NEW="R86 R87 R88 Q9 C82 U17 R106 D7 C81 R107 Q10 R89 C83 R109 U18 R110 R108 C84 U16 R85".split()
for r in NEW:
    f=a.FindFootprintByReference(r);g=b.FindFootprintByReference(r)
    t,u=f.Reference(),g.Reference()
    t.SetPosition(u.GetPosition());t.SetLayer(u.GetLayer());t.SetVisible(u.IsVisible())
    t.SetTextSize(u.GetTextSize());t.SetTextThickness(u.GetTextThickness());t.SetTextAngle(u.GetTextAngle())
a.Save(sys.argv[3])

import pcbnew,sys
src,dst=sys.argv[1],sys.argv[2]
b=pcbnew.LoadBoard(src)
LIB="/usr/share/kicad/footprints/"
SW={"F1":("Fuse.pretty","Fuse_1206_3216Metric","Fuse","7A 63V 1206"),
    "L2":("Inductor_SMD.pretty","L_Sunlord_SWPA5040S","Inductor_SMD","47u 1A"),
    "L3":("Inductor_SMD.pretty","L_Sunlord_SWPA5040S","Inductor_SMD","47u 1A")}
io=pcbnew.PCB_IO_MGR.PluginFind(pcbnew.PCB_IO_MGR.KICAD_SEXP) if hasattr(pcbnew,'PCB_IO_MGR') else None
for ref,(lib,name,nick,val) in SW.items():
    old=b.FindFootprintByReference(ref)
    new=pcbnew.FootprintLoad(LIB+lib,name)
    new.SetFPID(pcbnew.LIB_ID(nick,name))
    new.SetReference(ref); new.SetValue(val)
    new.SetPosition(old.GetPosition()); new.SetOrientation(old.GetOrientation())
    new.SetPath(old.GetPath())
    nets={p.GetNumber():p.GetNet() for p in old.Pads()}
    oldpads={p.GetNumber():p.GetPosition() for p in old.Pads()}
    # copy ref text position/attrs
    r_old=old.Reference(); r_new=new.Reference()
    r_new.SetPosition(r_old.GetPosition()); r_new.SetTextAngle(r_old.GetTextAngle())
    r_new.SetTextSize(r_old.GetTextSize()); r_new.SetTextThickness(r_old.GetTextThickness()); r_new.SetVisible(r_old.IsVisible())
    try: new.SetProperties(old.GetProperties())
    except Exception as e: print("props",e)
    new.SetAttributes(old.GetAttributes())
    b.Remove(old); b.Add(new)
    for p in new.Pads():
        p.SetNet(nets[p.GetNumber()])
        # stub from old pad center if old center not inside new pad
        op=oldpads[p.GetNumber()]
        if not p.HitTest(op):
            t=pcbnew.PCB_TRACK(b); t.SetStart(op); t.SetEnd(p.GetPosition()); t.SetLayer(pcbnew.F_Cu)
            t.SetWidth(pcbnew.FromMM(1.75)); t.SetNet(p.GetNet()); b.Add(t)
            print(ref,"stub",p.GetNumber(),[round(pcbnew.ToMM(v),2) for v in (op.x,op.y,p.GetPosition().x,p.GetPosition().y)])
b.BuildConnectivity()
f=pcbnew.ZONE_FILLER(b); f.Fill(b.Zones())
b.Save(dst); print("saved",dst)

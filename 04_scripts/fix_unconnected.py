"""Close remaining unconnected items with short DRC-checked tracks / via-in-pad. Usage: fix_unconnected.py in out"""
import re, sys
import pcbnew

mm, MM = pcbnew.FromMM, pcbnew.ToMM


def drc(b, path="/tmp/fix_drc.rpt"):
    pcbnew.WriteDRCReport(b, path, pcbnew.EDA_UNITS_MILLIMETRES, True)
    t = open(path).read()
    bad = len(re.findall(r"\[(clearance|shorting_items|tracks_crossing|hole_clearance|copper_edge_clearance|solder_mask_bridge|via_dangling|track_dangling|items_not_allowed|hole_near_hole|holes_co_located|drill_out_of_range|annular_width)\]", t))
    unc = []
    for blk in t.split("[unconnected_items]")[1:]:
        pts = re.findall(r"@\(([\d.]+) mm, ([\d.]+) mm\): (\w+)[^\[]*\[([^\]]+)\]", blk.split("\n[")[0])
        if len(pts) >= 2:
            unc.append(((float(pts[0][0]), float(pts[0][1])), (float(pts[1][0]), float(pts[1][1])), pts[0][3], pts[0][2], pts[1][2]))
    return bad, unc


def run(src, dst):
    b = pcbnew.LoadBoard(src)
    filler = pcbnew.ZONE_FILLER(b)
    base_bad, unc = drc(b)
    print("start: violations", base_bad, "unconnected", len(unc))
    for rnd in range(3):
        for (a, c, net, ta, tc) in unc:
            ni = b.FindNet(net)
            done = False
            # EP pads: via in pad to the In1 plane
            for (pt, typ) in ((a, ta), (c, tc)):
                if typ != "Pad" or net not in ("GND", "GNDP", "GND_ISO"):
                    continue
                pad = None
                for fp in b.GetFootprints():
                    for pd in fp.Pads():
                        if abs(MM(pd.GetPosition().x) - pt[0]) < 0.01 and abs(MM(pd.GetPosition().y) - pt[1]) < 0.01:
                            pad = pd
                if pad and MM(pad.GetSize().x) > 2.0 and MM(pad.GetSize().y) > 2.0:
                    v = pcbnew.PCB_VIA(b); v.SetPosition(pad.GetPosition()); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3))
                    v.SetNet(ni); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); b.Add(v)
                    filler.Fill(b.Zones()); bad, _ = drc(b)
                    if bad <= base_bad:
                        done = True; break
                    b.Remove(v)
            if done:
                continue
            routes = [[a, c], [a, (c[0], a[1]), c], [a, (a[0], c[1]), c]]
            for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
                if done:
                    break
                for path in routes:
                    items = []
                    if layer == pcbnew.B_Cu:      # drop vias at both ends
                        for q in (a, c):
                            v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(mm(q[0]), mm(q[1])))
                            v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetNet(ni); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                            b.Add(v); items.append(v)
                    for p, q in zip(path, path[1:]):
                        if p == q:
                            continue
                        tr = pcbnew.PCB_TRACK(b)
                        tr.SetStart(pcbnew.VECTOR2I(mm(p[0]), mm(p[1]))); tr.SetEnd(pcbnew.VECTOR2I(mm(q[0]), mm(q[1])))
                        tr.SetWidth(mm(0.25)); tr.SetLayer(layer); tr.SetNet(ni); b.Add(tr); items.append(tr)
                    filler.Fill(b.Zones())
                    bad, _ = drc(b)
                    if bad <= base_bad:
                        done = True
                        break
                    for it in items:
                        b.Remove(it)
            print(("fixed " if done else "FAILED ") + f"{net} {a} -> {c}")
        filler.Fill(b.Zones())
        base_bad, unc = drc(b)
        print(f"round {rnd}: violations {base_bad}, unconnected {len(unc)}")
        if not unc:
            break
    pcbnew.SaveBoard(dst, b)


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])

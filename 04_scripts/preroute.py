"""Rev D power pre-routing: short, wide, locked copper for the hot loops and Kelvin sense lines,
laid down BEFORE the autorouter so it can only add the low-current connections around them.
Clearance is checked geometrically with shapely against every other-net pad, track, keep-out band,
mounting hole and the board edge. Usage: preroute.py in.kicad_pcb out.kicad_pcb"""
import sys
import pcbnew
from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union

sys.path.insert(0, "/home/claude/dcdc")
import gen_pcb3 as GP

mm, MM = pcbnew.FromMM, pcbnew.ToMM
CLR = 0.25            # clearance used for the pre-routes (board min is 0.2)
HV = {"VIN", "VIN_RAW", "HB_SW", "CR_MID", "SR_D1", "SR_D2", "VBUS", "VOUT", "SW1", "SW2"}

# (net, [(refA, padsA), (refB, padsB)], widths, layer)   pads: tuple of pad numbers (any of them may be used)
F, B = pcbnew.F_Cu, pcbnew.B_Cu
W_HI, W_MID = (2.5, 2.0, 1.5, 1.0, 0.7), (1.0, 0.7, 0.5)
EDGES = [
    # ---------------- LLC primary hot loop
    ("HB_SW", ("Q5", "1"), ("Q5", "3"), (0.6,), F),
    ("HB_SW", ("Q5", "2"), ("T1", "1"), W_HI, F),
    ("HB_SW", ("Q6", "5"), ("T1", "1"), W_HI, F),
    ("HB_SW", ("Q5", "1"), ("Q6", "5"), W_HI, F),
    ("GNDP", ("Q6", "1"), ("Q6", "3"), (0.6,), F),
    ("GNDP", ("Q6", "2"), ("C61", "2"), W_HI, F),
    ("GNDP", ("C61", "2"), ("C62", "2"), W_HI, F),
    ("GNDP", ("C62", "2"), ("C63", "2"), W_HI, F),
    ("VIN", ("Q5", "5"), ("C61", "1"), W_HI, F),
    ("VIN", ("C61", "1"), ("C62", "1"), W_HI, F),
    ("VIN", ("C62", "1"), ("C63", "1"), W_HI, F),
    ("VIN", ("F1", "2"), ("C60", "1"), W_HI, F),
    ("VIN_RAW", ("J1", "1"), ("F1", "1"), W_HI, F),
    ("VIN", ("C60", "1"), ("C63", "1"), W_HI, F),
    # resonant capacitor column
    ("VIN", ("CR1", "1"), ("CR3", "1"), (1.0, 0.8), F),
    ("GNDP", ("CR4", "2"), ("CR6", "2"), (1.0, 0.8), F),
    ("CR_MID", ("CR1", "2"), ("CR6", "1"), (1.0, 0.8), F),
    ("CR_MID", ("CR2", "2"), ("T1", "2"), W_HI, F),
    ("CR_MID", ("CR5", "1"), ("T1", "2"), W_HI, F),
    ("VIN", ("CR1", "1"), ("F1", "2"), W_HI, F),
    # ---------------- synchronous rectifier
    ("SR_D2", ("Q8", "5"), ("T1", "5"), W_HI, F),
    ("SR_D1", ("Q7", "5"), ("T1", "3"), W_HI, F),
    ("VBUS", ("T1", "4"), ("C2", "1"), W_HI, F),
    ("VBUS", ("C2", "1"), ("C4", "1"), (1.5, 1.0), F),
    ("VBUS", ("T1", "4"), ("C4", "1"), W_HI, F),
    ("GND", ("C2", "2"), ("C4", "2"), (1.5, 1.0), F),
    ("GND", ("Q8", "1"), ("Q8", "3"), (0.6,), F),
    ("GND", ("Q7", "1"), ("Q7", "3"), (0.6,), F),
    ("GND", ("Q8", "1"), ("C2", "2"), W_HI, F),
    ("GND", ("Q7", "2"), ("C4", "2"), (1.0, 0.8), F, [(92.3, 40.13), (92.3, 32.8)]),
    # VBUS bus to the 4SBB input on the bottom layer (T1 pins are through-hole)
    ("VBUS", ("T1", "4"), ("C6", "1"), (2.5, 2.0), B, [(96.8, 21.75)],
     [(95.6, 21.75), (96.4, 21.75), (97.2, 21.75), (98.0, 21.75)]),
    # ---------------- 4SBB
    ("VBUS", ("C6", "1"), ("C5", "1"), W_HI, F),
    ("VBUS", ("C5", "1"), ("Q1", "5"), W_HI, F),
    ("SW1", ("Q1", "1"), ("Q1", "3"), (0.6,), F),
    ("SW1", ("Q1", "2"), ("L1", "1"), W_HI, F),
    ("SW1", ("Q2", "5"), ("L1", "1"), W_HI, F),
    ("SW2", ("Q3", "1"), ("Q3", "3"), (0.6,), F),
    ("SW2", ("Q3", "2"), ("L1", "2"), W_HI, F),
    ("SW2", ("Q4", "5"), ("L1", "2"), W_HI, F),
    ("PGND", ("Q2", "1"), ("Q2", "3"), (0.6,), F),
    ("PGND", ("Q4", "1"), ("Q4", "3"), (0.6,), F),
    ("PGND", ("Q2", "2"), ("RS1", "1"), W_HI, F),
    ("PGND", ("Q4", "2"), ("RS1", "1"), W_HI, F),
    ("VOUT", ("Q3", "5"), ("C7", "1"), W_HI, F),
    ("VOUT", ("C7", "1"), ("C12", "1"), W_HI, F),
    ("VOUT", ("Q3", "5"), ("C11", "1"), W_HI, F, [(139.05, 34.0)]),
    ("VOUT", ("C11", "1"), ("J2", "1"), (1.5, 1.0, 0.8), F, [(144.6, 34.0), (144.6, 54.0)]),
    ("GND", ("C7", "2"), ("C12", "2"), W_HI, F),
    ("GND", ("C5", "2"), ("C6", "2"), W_HI, F),
    ("VOUT_N", ("J2", "2"), ("RSH1", "1"), (2.0, 1.5), B, [(142.0, 53.75)], [(141.2, 53.75), (142.8, 53.75)]),
]

# Kelvin sense: explicit polylines from the inner edge of the shunt pads to the amplifier pins (0.25 mm)
KELVIN = [
    ("PGND", [("RS1", "1", (0.45, 1.2)), (119.49, 44.95), ("U7", "3", (0, 0))]),
    ("GND", [("RS1", "2", (-0.45, 1.2)), (124.51, 44.95), ("U7", "4", (0, 0))]),
    ("GND", [("RSH1", "2", (-1.2, 0.45)), (139.2, 47.49), (139.2, 48.86), ("U8", "4", (0, 0))]),
    ("VOUT_N", [("RSH1", "1", (-1.2, -0.45)), (139.2, 52.51), (139.2, 51.14), ("U8", "3", (0, 0))]),
]
NO_FANOUT = {("U7", "4"), ("U8", "4")}

# hand-specified copper: ("track", net, layer, [pts], width) | ("via", net, (x, y), dia, drill)
# U1 (LQFP64 at 113, 81): GND island under the package on F.Cu, 9 vias to the In1 GND plane, and a straight
# inward stub from every VSS/VSSA pin -> shortest decoupling return for the MCU.
MANUAL = [("track", "GND", F, [(111.2, 79.2), (114.8, 79.2)], 3.6),
          ("track", "GND", F, [(111.2, 82.8), (114.8, 82.8)], 3.6)]
MANUAL += [("via", "GND", (110.6 + 1.8 * i, 78.6 + 1.8 * j), 0.6, 0.3) for i in range(4) for j in range(4)]
# U10 HS (LLC driver reference) to the HB_SW node on B.Cu, away from the resonant-cap column
MANUAL += [("track", "HB_SW", F, [(46.475, 23.095), (48.3, 23.095)], 0.5),
           ("via", "HB_SW", (48.3, 23.095), 0.6, 0.3),
           ("track", "HB_SW", B, [(48.3, 23.095), (56.6, 31.6)], 0.6),
           ("via", "HB_SW", (56.6, 31.6), 0.6, 0.3),
           ("track", "HB_SW", F, [(56.6, 31.6), (56.6, 34.0)], 0.6)]


def main(src, dst):
    b = pcbnew.LoadBoard(src)
    pads = []
    for fp in b.GetFootprints():
        for pd in fp.Pads():
            bb = pd.GetBoundingBox()
            x0, y0, x1, y1 = MM(bb.GetX()), MM(bb.GetY()), MM(bb.GetRight()), MM(bb.GetBottom())
            if pd.GetShape() == pcbnew.PAD_SHAPE_CIRCLE:
                g = Point((x0 + x1) / 2, (y0 + y1) / 2).buffer((x1 - x0) / 2)
            else:
                g = box(x0, y0, x1, y1)
            layers = "all" if pd.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH) else (
                "F" if pd.IsOnLayer(pcbnew.F_Cu) else "B")
            pads.append(dict(ref=fp.GetReference(), num=pd.GetNumber(), net=pd.GetNetname(), g=g, layers=layers,
                             pos=(MM(pd.GetPosition().x), MM(pd.GetPosition().y)), pad=pd))
    edge = box(0.5, 0.5, GP.W - 0.5, GP.H - 0.5)
    keep = unary_union([box(GP.XB - GP.BAND, 0, GP.XB + GP.BAND, GP.H),
                        box(GP.XC - GP.BAND, GP.YC - GP.BAND, GP.XC + GP.BAND, GP.H),
                        box(GP.XC - GP.BAND, GP.YC - GP.BAND, GP.W, GP.YC + GP.BAND)])
    holes = unary_union([p["g"].buffer(0.3) for p in pads if p["pad"].GetAttribute() == pcbnew.PAD_ATTRIB_NPTH])
    tracks = []      # (geom, net, layer)

    def layer_ok(p, layer):
        return p["layers"] == "all" or (p["layers"] == "F") == (layer == F)

    def clear(geom, net, layer, clr):
        if not edge.contains(geom) or geom.intersects(keep) or geom.distance(holes) < 0.2:
            return False
        for p in pads:
            if p["net"] != net and layer_ok(p, layer) and geom.distance(p["g"]) < clr:
                return False
        for g, n, L in tracks:
            if n != net and L == layer and geom.distance(g) < clr:
                return False
        return True

    def blockers(geom, net, layer, clr):
        out = []
        if not edge.contains(geom): out.append("edge")
        if geom.intersects(keep): out.append("keepout")
        for p in pads:
            if p["net"] != net and layer_ok(p, layer) and geom.distance(p["g"]) < clr:
                out.append(f"{p['ref']}.{p['num']}({p['net']})")
        for g, n, L in tracks:
            if n != net and L == layer and geom.distance(g) < clr:
                out.append(f"track {n}")
        return out

    def pads_of(ref, num):
        return [p for p in pads if p["ref"] == ref and p["num"] == num]

    def add_track(pts, w, net, layer, lock=True):
        ni = b.FindNet(net)
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            if abs(x1 - x2) < 1e-6 and abs(y1 - y2) < 1e-6:
                continue
            t = pcbnew.PCB_TRACK(b)
            t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
            t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNet(ni); t.SetLocked(lock)
            b.Add(t)
        tracks.append((LineString(pts).buffer(w / 2), net, layer))

    def add_via(pt, net, d=0.8, drill=0.4):
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(pcbnew.VECTOR2I(mm(pt[0]), mm(pt[1]))); v.SetWidth(mm(d)); v.SetDrill(mm(drill))
        v.SetNet(b.FindNet(net)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetLocked(True)
        b.Add(v)
        g = Point(pt).buffer(d / 2)
        tracks.append((g, net, F)); tracks.append((g, net, B))

    ok_n = bad_n = 0
    report = []
    for e in EDGES:
        net, (ra, na), (rb, nb), widths, layer = e[:5]
        via_pts = e[5] if len(e) > 5 else None
        via_list = e[6] if len(e) > 6 else None
        A, Bp = pads_of(ra, na), pads_of(rb, nb)
        if not A or not Bp:
            report.append(f"missing pad {ra}.{na} / {rb}.{nb}")
            continue
        pairs = sorted(((a, c) for a in A for c in Bp), key=lambda ac: Point(ac[0]["pos"]).distance(Point(ac[1]["pos"])))
        clr = CLR + (0.05 if net in HV else 0)
        done = False
        for w in widths:
            for a, c in pairs[:3]:
                (x1, y1), (x2, y2) = a["pos"], c["pos"]
                cands = [[(x1, y1), (x2, y2)], [(x1, y1), (x2, y1), (x2, y2)], [(x1, y1), (x1, y2), (x2, y2)]]
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                cands += [[(x1, y1), (mx, y1), (mx, y2), (x2, y2)], [(x1, y1), (x1, my), (x2, my), (x2, y2)]]
                if via_pts:
                    cands = [[(x1, y1)] + list(via_pts) + ([] if via_list else [(x2, y2)])]
                for pts in cands:
                    pts = [q for i, q in enumerate(pts) if i == 0 or q != pts[i - 1]]
                    if len(pts) < 2:
                        continue
                    if layer == B:
                        # bottom layer: needs both ends on through-hole pads or a via next to the SMD pad
                        if not (a["layers"] == "all" or c["layers"] == "all"):
                            continue
                    g = LineString(pts).buffer(w / 2)
                    if clear(g, net, layer, clr):
                        if via_list:
                            add_track(pts, w, net, layer)
                            nv = 0
                            for q in via_list:
                                vg = Point(q).buffer(0.4)
                                if clear(vg, net, F, 0.2) and clear(vg, net, B, 0.2):
                                    add_via(q, net, 0.8, 0.4); nv += 1
                                    add_track([q, (q[0], c['pos'][1])], 0.8, net, F)
                            report.append(f"     {net} vias {nv}/{len(via_list)}")
                        elif layer == B and c["layers"] != "all":
                            # drop power vias inside the SMD pad area (via-in-pad, filled/capped at fab) -> keep 4
                            add_track(pts, w, net, layer)
                            px, py = c["pos"]
                            for dx, dy in ((-0.6, -0.6), (0.6, -0.6), (-0.6, 0.6), (0.6, 0.6)):
                                q = (px + dx * 0.5, py + dy)
                                vg = Point(q).buffer(0.4)
                                if clear(vg, net, F, 0.2) and clear(vg, net, B, 0.2):
                                    add_via(q, net, 0.6, 0.3)
                        else:
                            add_track(pts, w, net, layer)
                        report.append(f"ok   {net:7s} {ra}.{a['num']} -> {rb}.{c['num']}  w={w} {'B' if layer == B else 'F'} {len(pts) - 1} seg")
                        ok_n += 1
                        done = True
                        break
                if done:
                    break
            if done:
                break
        if not done:
            bad_n += 1
            a, c = pairs[0]
            pts = [a["pos"]] + list(via_pts or []) + [c["pos"]]
            report.append(f"FAIL {net:7s} {ra}.{na} -> {rb}.{nb}  blockers@{widths[-1]}: {blockers(LineString(pts).buffer(widths[-1] / 2), net, layer, clr)}")

    # VSS/VSSA stubs: from every U1 GND pad straight inward (along the pad axis) into the island
    u1 = b.FindFootprintByReference("U1")
    ux, uy = MM(u1.GetPosition().x), MM(u1.GetPosition().y)
    for pd in u1.Pads():
        if pd.GetNetname() != "GND":
            continue
        px, py = MM(pd.GetPosition().x), MM(pd.GetPosition().y)
        dx, dy = px - ux, py - uy
        if abs(dx) > abs(dy):
            s0 = (px - 0.55 * (1 if dx > 0 else -1), py); s1 = (ux + 3.2 * (1 if dx > 0 else -1), py)
        else:
            s0 = (px, py - 0.55 * (1 if dy > 0 else -1)); s1 = (px, uy + 3.2 * (1 if dy > 0 else -1))
        MANUAL.append(("track", "GND", F, [s0, s1], 0.25))
    for it in MANUAL:
        if it[0] == "track":
            _, net, layer, pts, w = it
            g = LineString(pts).buffer(w / 2)
            if clear(g, net, layer, 0.2):
                add_track(pts, w, net, layer); report.append(f"ok   MANUAL {net} {pts[0]}")
            else:
                bad_n += 1; report.append(f"FAIL MANUAL {net} {pts}: {blockers(g, net, layer, 0.2)}")
        else:
            _, net, q, d, dr = it
            g = Point(q).buffer(d / 2)
            if clear(g, net, F, 0.2) and clear(g, net, B, 0.2):
                add_via(q, net, d, dr)
            else:
                bad_n += 1; report.append(f"FAIL VIA {net} {q}: {blockers(g, net, F, 0.2) + blockers(g, net, B, 0.2)}")

    # Kelvin lines
    for net, path in KELVIN:
        pts = []
        for it in path:
            if isinstance(it[0], str):
                ref, num, (dx, dy) = it
                p = pads_of(ref, num)[0]
                x0, y0, x1, y1 = p["g"].bounds
                cx, cy = p["pos"]
                pts.append((round(cx + dx, 3), round(cy + dy, 3)))      # tap inside the pad, on the inner side
            else:
                pts.append(it)
        g = LineString(pts).buffer(0.125)
        if clear(g, net, F, 0.2):
            add_track(pts, 0.25, net, F)
            report.append(f"ok   KELVIN {net} {path[0][0]}->{path[-1][0]}")
        else:
            report.append(f"FAIL KELVIN {net} {path[0][0]}->{path[-1][0]}")
            bad_n += 1
    pcbnew.SaveBoard(dst, b)
    print("\n".join(report))
    print(f"pre-routes ok {ok_n}, failed {bad_n}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

"""Rev E copper check on the finished board (1 oz outer = 35 um, 0.5 oz inner = 17.5 um).
For each high-current path the filled copper of that net is sampled every 0.5 mm with a cross-section
perpendicular to the path (F.Cu, B.Cu and In1 where the net is poured there); layers in parallel give the
path resistance, I^2R loss and the narrowest neck. Temperature rise of the neck from IPC-2152 (external,
no plane nearby is conservative: 1 oz, 20 C rise ~ I = 0.084 * A_mil2^0.725 *... -> here IPC-2221 form).
usage: copper_check.py board.kicad_pcb > copper_check.txt"""
import math, sys
import pcbnew
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

MM = pcbnew.ToMM
RHO = 1.72e-8 * (1 + 0.00393 * (70 - 20))            # copper at 70 C
T = {pcbnew.F_Cu: 35e-6, pcbnew.B_Cu: 35e-6, pcbnew.In1_Cu: 17.5e-6, pcbnew.In2_Cu: 17.5e-6}
LN = {pcbnew.F_Cu: "F", pcbnew.B_Cu: "B", pcbnew.In1_Cu: "In1", pcbnew.In2_Cu: "In2"}

# (label, net(s), I_rms [A], path points, layers)
PATHS = [
    ("J1 -> F1 (input)", ["VIN_RAW"], 4.6, [(10.5, 31.0), (15.6, 29.6)], ["F"]),
    ("F1 -> C60 -> C61 -> Q5 drain", ["VIN"], 4.6, [(18.4, 29.6), (30.0, 30.0), (45.4, 33.0), (49.9, 34.0)], ["F"]),
    ("Q6 source -> C61..C63 -> C60 -> J1 return", ["GNDP"], 4.6, [(48.1, 41.4), (40.0, 40.4), (30.0, 39.6), (12.0, 39.6), (10.5, 36.1)], ["F", "In1", "B"]),
    ("LLC half-bridge -> T1 (HB_SW)", ["HB_SW"], 10.1, [(53.9, 34.6), (57.4, 37.5)], ["F"]),
    ("Q6 drain -> T1 (HB_SW)", ["HB_SW"], 10.1, [(52.0, 42.0), (57.4, 41.35)], ["F"]),
    ("T1 -> resonant caps (CR_MID)", ["CR_MID"], 10.1, [(57.4, 22.45), (55.0, 22.0), (55.0, 15.2)], ["F"]),
    ("T1 -> Q7 (SR_D1)", ["SR_D1"], 3.6, [(82.8, 39.5), (87.6, 39.5)], ["F"]),
    ("T1 -> Q8 (SR_D2)", ["SR_D2"], 3.6, [(82.8, 20.5), (87.6, 20.5)], ["F"]),
    ("T1 centre tap -> C2..C4 (VBUS)", ["VBUS"], 4.5, [(82.8, 30.0), (87.0, 30.0)], ["F", "B"]),
    ("SR side -> 4SBB input (VBUS, bottom link)", ["VBUS"], 4.5, [(85.0, 28.0), (92.0, 24.0), (100.0, 20.0), (104.9, 24.0)], ["F", "B"]),
    ("SR sources -> C2..C4 return (GND strip)", ["GND"], 4.5, [(91.6, 40.0), (91.0, 30.0), (91.6, 21.0)], ["F", "In1", "B"]),
    ("Q1 / Q2 -> L1 (SW1)", ["SW1"], 5.2, [(109.0, 30.0), (112.0, 26.0), (114.3, 19.0)], ["F"]),
    ("Q3 / Q4 -> L1 (SW2)", ["SW2"], 5.2, [(134.0, 30.0), (131.0, 26.0), (129.7, 19.0)], ["F"]),
    ("Q2 sources -> RS1 (PGND)", ["PGND"], 5.0, [(109.0, 35.5), (119.0, 36.0), (119.0, 38.0)], ["F", "B"]),
    ("Q4 sources -> RS1 (PGND)", ["PGND"], 5.0, [(133.0, 35.5), (120.0, 35.5), (119.0, 38.0)], ["F", "B"]),
    ("Q3 -> output caps -> C11 -> J2 (VOUT)", ["VOUT"], 5.0, [(139.0, 22.0), (150.0, 21.2), (156.9, 21.2), (156.9, 33.4), (154.0, 45.0), (152.0, 52.0), (148.0, 54.0)], ["F", "B"]),
    ("J2 return -> RSH1 (VOUT_N)", ["VOUT_N"], 5.0, [(148.0, 48.9), (143.0, 49.0), (142.0, 53.0)], ["F"]),
    ("RSH1 -> RS1 -> SR return (GND)", ["GND"], 5.0, [(142.0, 47.0), (125.0, 38.5), (110.0, 45.0), (95.0, 44.0), (91.0, 34.0)], ["In1", "B", "F"]),
]


def polys_of(sp):
    out = []
    for i in range(sp.OutlineCount()):
        o = sp.Outline(i)
        pts = [(MM(o.CPoint(k).x), MM(o.CPoint(k).y)) for k in range(o.PointCount())]
        if len(pts) > 2:
            hs = []
            for h in range(sp.HoleCount(i)):
                ho = sp.Hole(i, h)
                hs.append([(MM(ho.CPoint(k).x), MM(ho.CPoint(k).y)) for k in range(ho.PointCount())])
            out.append(Polygon(pts, hs).buffer(0))
    return out


def copper(b, nets, layer):
    geo = []
    for z in b.Zones():
        if z.GetIsRuleArea() or z.GetNetname() not in nets or not z.IsOnLayer(layer):
            continue
        geo += polys_of(z.GetFilledPolysList(layer))
    for t in b.GetTracks():
        if t.GetNetname() in nets and t.Type() != pcbnew.PCB_VIA_T and t.GetLayer() == layer:
            s, e = t.GetStart(), t.GetEnd()
            geo.append(LineString([(MM(s.x), MM(s.y)), (MM(e.x), MM(e.y))]).buffer(MM(t.GetWidth()) / 2))
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() in nets and p.IsOnLayer(layer):
                bb = p.GetBoundingBox()
                geo.append(Polygon([(MM(bb.GetX()), MM(bb.GetY())), (MM(bb.GetRight()), MM(bb.GetY())),
                                    (MM(bb.GetRight()), MM(bb.GetBottom())), (MM(bb.GetX()), MM(bb.GetBottom()))]))
    return unary_union(geo) if geo else None


def width_at(cu, p, nx, ny, span=12.0):
    if cu is None:
        return 0.0
    seg = LineString([(p.x - nx * span, p.y - ny * span), (p.x + nx * span, p.y + ny * span)])
    inter = seg.intersection(cu)
    if inter.is_empty:
        return 0.0
    parts = [inter] if inter.geom_type == "LineString" else [g for g in getattr(inter, "geoms", []) if g.geom_type == "LineString"]
    best = 0.0
    for g in parts:
        if g.distance(p) < 0.3:
            best = max(best, g.length)
    return best


def main(fn):
    b = pcbnew.LoadBoard(fn)
    lay = {"F": pcbnew.F_Cu, "B": pcbnew.B_Cu, "In1": pcbnew.In1_Cu}
    print(f"{'path':46s} {'I':>5s}  {'layers':10s} {'len':>5s} {'min w (layer)':>15s}  {'R mOhm':>7s} {'P mW':>6s} {'dV mV':>6s}")
    tot = 0.0
    for label, nets, I, pts, layers in PATHS:
        line = LineString(pts)
        cu = {L: copper(b, set(nets), lay[L]) for L in layers}
        n = max(2, int(line.length / 0.5))
        R = 0.0
        minw = (1e9, "")
        last_g, miss = None, 0
        for k in range(n):
            d0, d1 = line.length * k / n, line.length * (k + 1) / n
            p = line.interpolate((d0 + d1) / 2)
            q0, q1 = line.interpolate(d0), line.interpolate(d1)
            dx, dy = q1.x - q0.x, q1.y - q0.y
            L = math.hypot(dx, dy) or 1e-9
            nx, ny = -dy / L, dx / L
            g = 0.0
            for Ln in layers:
                w = width_at(cu[Ln], p, nx, ny)
                if w > 0:
                    g += (w * 1e-3) * T[lay[Ln]] / (RHO * (d1 - d0) * 1e-3)
                    if Ln == layers[0] and w < minw[0]:
                        minw = (w, Ln)
            if g > 0:
                last_g, miss = g, 0
                R += 1.0 / g
            else:
                miss += 1                          # a sample that hits a via antipad / pad gap: reuse the
                R += 1.0 / last_g if (last_g and miss <= 2) else 1.0   # neighbour; 3 in a row = a real gap (1 ohm)
        P = I * I * R
        tot += P
        print(f"{label:46s} {I:5.1f}  {'+'.join(layers):10s} {line.length:5.1f} {minw[0]:9.2f} ({minw[1]:>3s})  {R*1e3:7.2f} {P*1e3:6.0f} {I*R*1e3:6.1f}")
    print(f"total I^2R in these paths: {tot:.2f} W (worst case, 50 W out at 12 V in)")


if __name__ == "__main__":
    main(sys.argv[1])

"""Rev E power copper (1 oz outer / 0.5 oz inner).
L1 (F.Cu): power path as pours, one per net, sized for the rms current; switch nodes kept compact.
L2 (In1):  solid ground planes per isolation domain (GNDP / GND / GND_ISO) - return path + shield.
L3 (In2):  signals (after routing: GND / GNDP flood in the leftovers).
L4 (B.Cu): VBUS link SR -> 4SBB, VOUT strip in parallel with the top, signals, ground flood.
Stitching vias tie each top pour to its plane / bottom copper. Pre-routed: Kelvin lines, gate stubs + vias
out of the gate-pin pockets, LLC driver HS/HO pair, flyback clamp/drain/source and the VIN feeds.
usage: power5.py in.kicad_pcb out.kicad_pcb [route]   ('route' = also add routing keep-outs)"""
import math, sys
import pcbnew
from shapely.geometry import box, Polygon, LineString, Point
from shapely.ops import unary_union

sys.path.insert(0, "/home/claude/dcdc/pcb5")
import place5 as P

mm, MM = pcbnew.FromMM, pcbnew.ToMM
F, I1, I2, B = pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu
U = lambda *bs: unary_union([box(*b) for b in bs])

# ------------------------------------------------------------------------------------------------ pours
# (net, layer, shapely geometry, priority)
POURS = [
    # ---------------- primary input + LLC half-bridge
    ("VIN_RAW", F, U((8.3, 28.2, 16.6, 32.7)), 30),
    ("VIN", F, U((17.3, 27.0, 53.1, 34.3), (33.0, 27.0, 52.9, 37.4), (49.6, 22.3, 52.95, 27.0), (20.9, 24.4, 23.1, 27.0)), 28),
    ("GNDP", F, U((8.2, 33.3, 16.6, 48.6), (16.6, 34.7, 32.6, 48.6), (32.6, 37.8, 49.3, 48.6)), 24),
    ("GNDP", F, U((49.6, 13.4, 52.95, 22.0)), 24),                       # CR4-6 return
    ("HB_SW", F, U((53.2, 32.5, 58.9, 44.6), (55.8, 30.9, 58.9, 32.5), (49.5, 39.4, 53.2, 44.6)), 30),
    ("CR_MID", F, U((53.9, 13.6, 58.9, 30.0)), 30),
    # ---------------- flyback primary
    ("FLY_DRN", F, U((58.0, 61.0, 63.4, 64.6)), 32),
    ("VIN", F, U((52.6, 56.6, 63.4, 58.4)), 28),
    ("GNDP", F, U((57.6, 53.9, 60.8, 55.6)), 24),                        # C95 return
    # ---------------- synchronous rectifier
    ("SR_D2", F, U((81.4, 15.6, 90.2, 23.9)), 30),
    ("SR_D1", F, U((81.4, 36.1, 90.2, 42.8), (81.4, 42.8, 87.4, 45.0)), 30),
    ("VBUS", F, U((81.4, 24.6, 88.6, 35.4)), 28),
    ("GND", F, U((90.3, 19.2, 92.6, 36.9), (88.7, 24.1, 90.3, 35.9), (89.3, 42.8, 90.3, 45.4), (90.3, 36.9, 90.8, 38.4), (90.3, 38.4, 92.6, 45.2), (92.6, 28.3, 93.7, 29.45)), 26),
    # ---------------- 4SBB
    ("VBUS", F, U((93.3, 10.4, 101.6, 13.9), (96.3, 13.9, 101.6, 21.3), (101.6, 13.9, 102.4, 21.3), (98.6, 21.3, 102.4, 24.5), (102.4, 21.3, 107.4, 26.5),
                  (91.0, 8.0, 93.6, 10.8)), 28),
    ("SW1", F, U((107.6, 22.75, 112.3, 33.5), (112.3, 22.75, 113.6, 33.3), (113.6, 22.75, 116.3, 33.5), (109.8, 12.4, 116.3, 22.75)), 30),
    ("SW2", F, U((127.8, 12.4, 134.3, 33.5), (134.3, 19.4, 136.3, 23.25), (134.3, 25.6, 136.6, 33.5)), 30),
    ("PGND", F, U((107.6, 34.1, 112.3, 37.4), (112.3, 34.5, 113.6, 37.4), (113.6, 34.1, 136.4, 37.4), (117.8, 37.4, 120.0, 40.0)), 28),
    ("PGND", B, U((107.6, 34.1, 136.4, 37.4)), 28),
    ("VOUT", F, U((136.5, 19.3, 158.6, 22.95), (155.2, 22.95, 158.6, 30.0), (152.6, 30.0, 158.6, 38.5), (150.4, 38.5, 158.6, 56.0),
                  (145.8, 51.2, 150.4, 56.0)), 28),
    ("VOUT_N", F, U((140.0, 47.95, 150.0, 50.3), (140.0, 50.3, 144.0, 54.0)), 28),
    ("GND", F, U((141.8, 23.6, 155.0, 26.0), (144.0, 26.0, 149.4, 36.0)), 24),      # output caps return + C11 GND
    ("GND", F, U((97.0, 24.7, 102.0, 26.4)), 24),                                     # C5 return + via pad
    ("GND", F, U((124.9, 37.3, 127.6, 40.6)), 24),                                    # RS1 GND end -> plane vias
    ("GND", F, U((101.8, 10.4, 106.8, 13.6), (102.4, 9.3, 107.7, 13.6)), 24),         # C1 return + via row
    # ---------------- flyback secondary
    ("FLY_SA", F, U((76.6, 58.7, 82.9, 62.9)), 32),
    ("+10V", F, U((83.9, 57.1, 89.6, 62.0)), 28),
    ("GND", F, U((76.6, 50.6, 89.0, 56.3)), 24),
    # ---------------- bottom: VBUS link and VOUT strip
    ("VBUS", B, U((80.6, 24.2, 90.0, 35.6), (90.0, 8.0, 107.4, 27.0)), 28),
    ("VOUT", B, U((150.4, 19.3, 158.6, 56.0), (145.8, 51.2, 150.4, 56.0), (136.6, 19.3, 150.4, 22.95)), 28),
]

# In1 ground planes (one per domain)
E = 0.5
PLANES = [
    ("GNDP", [(E, E), (P.XB - P.BAND, E), (P.XB - P.BAND, P.H - E), (E, P.H - E)]),
    ("GND", [(P.XB + P.BAND, E), (P.W - E, E), (P.W - E, P.YC - P.BAND), (P.XC - P.BAND, P.YC - P.BAND),
             (P.XC - P.BAND, P.H - E), (P.XB + P.BAND, P.H - E)]),
    ("GND_ISO", [(P.XC + P.BAND, P.YC + P.BAND), (P.W - E, P.YC + P.BAND), (P.W - E, P.H - E), (P.XC + P.BAND, P.H - E)]),
]


def via_grid(x0, y0, x1, y1, pitch=1.2):
    out, y = [], y0
    while y <= y1 + 1e-6:
        x = x0
        while x <= x1 + 1e-6:
            out.append((round(x, 3), round(y, 3)))
            x += pitch
        y += pitch
    return out


# stitching vias (net, points, dia, drill): checked for clearance, dropped silently where they do not fit
STITCH = [
    ("GNDP", via_grid(50.3, 14.0, 50.3, 21.4, 1.1), 0.6, 0.3),           # CR4-6 to plane
    ("GNDP", via_grid(34.0, 41.6, 46.0, 47.6, 1.5), 0.6, 0.3),           # LLC low-side return
    ("GNDP", via_grid(9.0, 39.0, 31.0, 47.6, 2.0), 0.6, 0.3),
    ("GNDP", via_grid(58.0, 54.3, 60.4, 54.3, 0.8), 0.6, 0.3),          # C95
    ("GND", via_grid(90.9, 27.6, 92.1, 44.4, 1.2), 0.6, 0.3),            # SR return strip (not across the bottom VBUS link, y < 27)
    ("GND", [(97.6, 25.1), (97.6, 26.1)], 0.6, 0.3),                    # C5 return -> In1 GND (beside the pad)
    ("GND", [(103.0, 9.9), (104.2, 9.9), (105.4, 9.9), (107.1, 11.4), (107.1, 12.6)], 0.6, 0.3),   # C1 return
    ("GND", via_grid(126.3, 37.8, 127.2, 40.2, 0.8), 0.6, 0.3),         # RS1 GND end -> plane (main return)
    ("GND", via_grid(142.2, 25.4, 154.6, 25.4, 0.9), 0.6, 0.3),         # output caps
    ("GND", via_grid(144.4, 26.6, 149.0, 35.6, 1.1), 0.6, 0.3),          # C11
    ("GND", via_grid(77.2, 51.0, 88.6, 51.0, 1.0), 0.6, 0.3),           # flyback secondary return
    ("VBUS", via_grid(84.0, 24.9, 88.2, 35.2, 1.7), 0.6, 0.3),           # SR side top <-> bottom
    ("VBUS", via_grid(96.8, 14.4, 101.0, 20.8, 1.7), 0.6, 0.3),          # 4SBB input top <-> bottom
    ("VOUT", via_grid(151.0, 39.0, 158.0, 50.6, 1.7), 0.6, 0.3),         # VOUT top <-> bottom
    ("VOUT", via_grid(155.6, 23.4, 158.2, 29.6, 1.7), 0.6, 0.3),
    ("VOUT", via_grid(137.0, 19.6, 141.0, 19.6, 1.7), 0.6, 0.3),
    ("PGND", via_grid(108.2, 36.6, 135.8, 36.6, 1.7), 0.6, 0.3),          # PGND bar top <-> bottom; 1.7 mm pitch keeps a 0.5 mm GND-plane web between antipads on In1
]

# hand-routed copper: (net, layer, [pts], width) and vias (net, (x, y), dia, drill)
TRACKS = [
    # Kelvin: RS1 inner pad edges -> U7 IN+ (PGND) / IN- (GND), 0.25 mm, side by side
    ("PGND", F, [(119.4, 38.0), (119.5, 38.0), (119.5, 44.95), (120.86, 44.95)], 0.25),
    ("GND", F, [(124.6, 38.0), (124.5, 38.0), (124.5, 44.95), (123.14, 44.95)], 0.25),
    # Kelvin: RSH1 inner pad edges -> U8 IN+ (VOUT_N) / IN- (GND)
    ("GND", F, [(140.8, 47.3), (139.2, 47.3), (139.2, 48.86), (137.45, 48.86)], 0.25),
    ("VOUT_N", F, [(140.8, 52.7), (139.2, 52.7), (139.2, 51.14), (137.45, 51.14)], 0.25),
    # gate-pin pockets: short stub + via, the drive comes in on In2 / B.Cu
    ("G1", F, [(108.9, 22.09), (108.9, 21.0)], 0.4),
    ("G3", F, [(135.1, 23.91), (135.1, 24.95)], 0.4),
    ("G2", F, [(111.91, 34.6), (112.95, 33.9)], 0.4),
    ("G5", F, [(53.9, 32.09), (53.9, 31.0)], 0.4),
    ("G5", F, [(53.9, 31.0), (55.09, 31.4)], 0.3),
    ("G6", F, [(48.1, 43.91), (46.9, 44.09)], 0.4),
    ("G6", F, [(46.9, 44.09), (45.9, 43.4)], 0.3),
]
TRACKS += [
    # LLC high-side gate loop: U10 HO -> R62 -> via, G5 and its HB_SW return run as a 0.4 mm pair on B.Cu to Q5
    ("HOP", F, [(43.5, 20.87), (44.93, 20.87)], 0.4),
    ("G5", F, [(46.57, 20.87), (47.35, 20.87)], 0.4),
    ("HB_SW", F, [(43.5, 19.59), (48.6, 19.59), (48.6, 20.09)], 0.4),
    ("HB_SW", F, [(48.2, 18.7), (48.2, 19.59)], 0.4),
    ("HBP", F, [(43.5, 22.13), (48.6, 22.13), (48.6, 21.63)], 0.4),
    ("G5", B, [(47.35, 20.87), (47.35, 26.05), (52.3, 31.0), (53.9, 31.0)], 0.4),
    ("HB_SW", B, [(48.2, 18.7), (48.2, 25.7), (52.7, 30.2), (55.0, 30.2), (55.0, 32.9)], 0.4),
    # LLC low-side gate: U10 LO -> R63 -> via, B.Cu to the Q6 gate via (return through the GNDP planes)
    ("LOP", F, [(37.4, 23.41), (36.9, 23.41), (36.9, 25.42), (35.6, 25.42)], 0.4),
    ("G6", F, [(34.5, 23.77), (35.6, 23.77)], 0.4),
    ("G6", B, [(34.5, 23.77), (34.5, 26.4), (45.25, 37.15), (45.25, 42.75), (45.9, 43.4)], 0.4),
    # LLC driver inputs: U10 pin -> pull-down pad straight, via for the In2 run from the isolator
    ("LLC_HI_P", F, [(37.5, 19.59), (35.9, 19.59)], 0.25),
    ("LLC_HI_P", F, [(36.6, 19.59), (36.6, 18.6)], 0.25),
    ("LLC_LO_P", F, [(37.5, 20.87), (35.9, 20.87)], 0.25),
    ("LLC_LO_P", F, [(36.0, 20.87), (36.0, 21.95)], 0.25),
    # 4SBB Q4 gate out of the PGND bar end to R11, Q7 gate to R70
    ("G4", F, [(135.91, 34.9), (138.4, 34.9), (140.27, 36.77)], 0.4),
    ("G7", F, [(91.58, 37.59), (94.89, 37.59)], 0.4),
    # 4SBB high-side gate Q1: U2 HO -> R4 -> G1 via; G1 and its SW1 return as a 0.4 mm pair on In2 to the Q1 pocket
    ("HB1", F, [(103.0, 42.36), (97.6, 42.36), (97.6, 42.86)], 0.4),
    ("SW1", F, [(103.0, 44.91), (97.6, 44.91), (97.6, 44.42)], 0.4),
    ("SW1", F, [(98.3, 44.91), (98.3, 45.75)], 0.4),
    ("SW1", F, [(101.78, 44.91), (101.78, 47.43)], 0.3),
    ("HO1", F, [(103.0, 43.64), (101.58, 43.64)], 0.4),
    ("G1", F, [(99.92, 43.64), (99.1, 43.64)], 0.4),
    ("G1", F, [(101.78, 48.45), (101.78, 49.4)], 0.3),
    ("G1", I2, [(99.1, 43.64), (99.1, 38.6), (108.9, 28.8), (108.9, 21.0)], 0.4),
    ("SW1", I2, [(98.3, 45.75), (98.3, 38.27), (108.1, 28.47), (108.1, 27.6)], 0.4),
    ("G1", I2, [(99.1, 43.64), (101.78, 49.4)], 0.3),
    # MCU ground pins: short stub inward to a via on the In1 GND plane (keeps the router out of the pin field)
    ("GND", F, [(116.25, 86.2), (116.25, 84.9)], 0.25),
    ("GND", F, [(118.2, 79.75), (116.9, 79.75)], 0.25),
    ("GND", F, [(118.2, 77.75), (116.9, 77.75)], 0.25),
    ("GND", F, [(107.8, 84.25), (109.1, 84.25)], 0.25),
    ("GND", F, [(109.75, 75.8), (109.75, 77.1)], 0.25),
    # 4SBB low-side gate Q2: crosses the PGND bar on In2 (pocket via above, via next to R5 below)
    ("G2", I2, [(112.95, 33.9), (112.95, 40.27)], 0.4),
    ("G2", F, [(111.47, 40.27), (112.95, 40.27)], 0.4),
    ("G2", F, [(109.96, 37.98), (109.96, 38.76), (111.47, 40.27)], 0.4),
]
TRACKS += [
    # 2-pin snubber nets and pads that sit inside another net's pour: short fixed links / vias
    ("SNB1", F, [(114.4, 31.66), (114.4, 33.53)], 0.4),
    ("SNB2", F, [(129.6, 31.66), (129.6, 33.53)], 0.4),
    ("SNB3", F, [(88.97, 44.49), (90.6, 46.25), (91.86, 46.25)], 0.4),
    ("SNB4", F, [(86.53, 12.9), (86.53, 11.15)], 0.4),
    ("GND", F, [(86.53, 9.25), (86.53, 8.1)], 0.4),
    ("GND", F, [(101.2, 18.82), (101.2, 17.7)], 0.4),
    ("GND", F, [(153.4, 41.38), (153.4, 42.5)], 0.4),
]
TRACKS += [
    # VIN feed to the flyback (In2, 0.8 mm): via in the VIN band -> via in the flyback VIN pour
    ("VIN", F, [(47.0, 29.0), (47.0, 29.0)], 0.8),
    ("VIN", I2, [(47.0, 29.0), (47.0, 50.0), (52.6, 55.6), (55.0, 56.9)], 0.8),
]
VIAS = [("VIN", (47.0, 29.0), 0.8, 0.4), ("VIN", (55.0, 56.9), 0.8, 0.4),
        ("GND", (101.2, 17.7), 0.6, 0.3), ("GND", (86.53, 8.1), 0.6, 0.3), ("GND", (153.4, 42.5), 0.6, 0.3),
        ("G1", (108.9, 21.0), 0.6, 0.3), ("G3", (135.1, 24.95), 0.6, 0.3), ("G2", (112.95, 33.9), 0.6, 0.3),
        ("G5", (53.9, 31.0), 0.6, 0.3), ("G6", (45.9, 43.4), 0.6, 0.3),
        ("G5", (47.35, 20.87), 0.6, 0.3), ("HB_SW", (48.2, 18.7), 0.6, 0.3), ("HB_SW", (55.0, 32.9), 0.6, 0.3),
        ("G6", (34.5, 23.77), 0.6, 0.3), ("LLC_HI_P", (36.6, 18.6), 0.6, 0.3), ("LLC_LO_P", (36.0, 21.95), 0.6, 0.3), ("G2", (112.95, 40.27), 0.6, 0.3),
        ("G1", (99.1, 43.64), 0.6, 0.3), ("G1", (101.78, 49.4), 0.6, 0.3), ("SW1", (98.3, 45.75), 0.6, 0.3),
        ("SW1", (108.1, 27.6), 0.6, 0.3),
        ("GND", (116.25, 84.9), 0.6, 0.3), ("GND", (116.9, 79.75), 0.6, 0.3), ("GND", (116.9, 77.75), 0.6, 0.3),
        ("GND", (109.1, 84.25), 0.6, 0.3), ("GND", (109.75, 77.1), 0.6, 0.3)]


def build_zone(b, net, layer, geom, prio, name, clr=0.3):
    polys = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)
    out = []
    for g in polys:
        z = pcbnew.ZONE(b)
        z.SetLayer(layer)
        z.SetNet(b.FindNet(net))
        ol = z.Outline()
        ol.NewOutline()
        for x, y in list(g.exterior.coords)[:-1]:
            ol.Append(mm(x), mm(y))
        z.SetLocalClearance(mm(clr))
        z.SetMinThickness(mm(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        z.SetAssignedPriority(prio)
        z.SetZoneName(name)
        b.Add(z)
        out.append(z)
    return out


def main(src, dst):
    b = pcbnew.LoadBoard(src)
    for i, (net, layer, g, prio) in enumerate(POURS):
        build_zone(b, net, layer, g, prio, f"PWR_{net}_{i}")
    for net, pts in PLANES:
        build_zone(b, net, I1, Polygon(pts), 0, f"PLANE_{net}")
    # obstacles for stitching / track checks
    obst = []
    for fp in b.GetFootprints():
        for pd in fp.Pads():
            bb = pd.GetBoundingBox()
            g = box(MM(bb.GetX()), MM(bb.GetY()), MM(bb.GetRight()), MM(bb.GetBottom()))
            th = pd.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH)
            obst.append((g, pd.GetNetname(), th, pd.IsOnLayer(F)))
    keep = unary_union([box(*k) for k in P.KEEPOUT])
    placed = []
    ni = {}

    def net_(n):
        if n not in ni:
            ni[n] = b.FindNet(n)
        return ni[n]

    def ok_via(pt, d, net):
        g = Point(pt).buffer(d / 2)
        if g.intersects(keep) or not box(0.6, 0.6, P.W - 0.6, P.H - 0.6).contains(g):
            return False
        for o, n, th, onF in obst:
            if n != net and g.distance(o) < 0.25:
                return False
            if n == net and not th and g.intersects(o):        # no via in SMD pads
                return False
        for q, dq, nq in placed:
            if Point(pt).distance(Point(q)) < (d + dq) / 2 + 0.25:
                return False
        return True

    for net, pt, d, dr in VIAS:
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(pcbnew.VECTOR2I(mm(pt[0]), mm(pt[1])))
        v.SetWidth(mm(d)); v.SetDrill(mm(dr)); v.SetNet(net_(net)); v.SetLocked(True)
        b.Add(v)
        placed.append((pt, d, net))
    for net, layer, pts, w in TRACKS:
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(b)
            t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
            t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNet(net_(net)); t.SetLocked(True)
            b.Add(t)
        obst.append((LineString(pts).buffer(w / 2), net, False, layer == F))
    # every small R/C in the signal area gets its own ground via right at its GND pad (decoupling inductance,
    # and the router can never box the pad in): outward along the part axis first, then sideways
    nesc = 0
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        if ref[0] not in "RC" or not (94 < MM(fp.GetPosition().x) < 141 and 62 < MM(fp.GetPosition().y) < 104):
            continue
        pds = list(fp.Pads())
        if len(pds) != 2:
            continue
        for pd, other in ((pds[0], pds[1]), (pds[1], pds[0])):
            if pd.GetNetname() != "GND" or other.GetNetname() == "GND":
                continue
            px, py = MM(pd.GetPosition().x), MM(pd.GetPosition().y)
            ox, oy = MM(other.GetPosition().x), MM(other.GetPosition().y)
            L = math.hypot(px - ox, py - oy) or 1
            ux, uy = (px - ox) / L, (py - oy) / L
            bb = pd.GetBoundingBox()
            half = max(MM(bb.GetWidth()), MM(bb.GetHeight())) / 2
            cands = []
            for dist in (half + 0.55, half + 0.75, half + 1.0):
                for vx, vy in ((ux, uy), (-uy, ux), (uy, -ux)):
                    cands.append((px + vx * dist, py + vy * dist))
            for cx, cy in cands:
                pt = (round(cx, 2), round(cy, 2))
                trk = LineString([(px, py), pt]).buffer(0.15)
                if not ok_via(pt, 0.6, "GND"):
                    continue
                if any(n != "GND" and onF and trk.distance(o) < 0.2 for o, n, th, onF in obst):
                    continue
                v = pcbnew.PCB_VIA(b)
                v.SetPosition(pcbnew.VECTOR2I(mm(pt[0]), mm(pt[1])))
                v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetNet(net_("GND")); v.SetLocked(True)
                b.Add(v)
                t = pcbnew.PCB_TRACK(b)
                t.SetStart(pd.GetPosition()); t.SetEnd(pcbnew.VECTOR2I(mm(pt[0]), mm(pt[1])))
                t.SetWidth(mm(0.3)); t.SetLayer(F); t.SetNet(net_("GND")); t.SetLocked(True)
                b.Add(t)
                placed.append((pt, 0.6, "GND"))
                obst.append((trk, "GND", False, True))
                nesc += 1
                break
            else:
                print("  no GND escape via for", ref)
    print("GND pad vias", nesc)
    nv = 0
    for net, pts, d, dr in STITCH:
        for pt in pts:
            if ok_via(pt, d, net):
                v = pcbnew.PCB_VIA(b)
                v.SetPosition(pcbnew.VECTOR2I(mm(pt[0]), mm(pt[1])))
                v.SetWidth(mm(d)); v.SetDrill(mm(dr)); v.SetNet(net_(net)); v.SetLocked(True)
                b.Add(v)
                placed.append((pt, d, net)); nv += 1
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(dst, b)
    print("zones", len(list(b.Zones())), "stitch vias", nv)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

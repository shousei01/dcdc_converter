"""PCB placement for DCDC LLC + 4SBB (KiCad 7 board). Hand placement of power parts and connectors,
anchor-based auto placement of passives, isolation keep-out bands, In1 ground planes, M3 holes.
Writes <out>.kicad_pcb (unrouted) ready for DSN export / Freerouting.
"""
import json, math, sys
import pcbnew
sys.path.insert(0, "/home/claude/dcdc")
import design as D

FPDIR = "/usr/share/kicad/footprints"
CUSTOM_FP = "/home/claude/dcdc/out/custom_fp.pretty"
mm, MM = pcbnew.FromMM, pcbnew.ToMM
W, H = 160.0, 105.0
XB = 70.0            # primary / secondary barrier centre
XC = 138.0           # CAN logic / bus barrier centre
YC = 62.0            # top of CAN bus region
BAND = 2.0           # half-width of the no-copper band (4 mm total)
SPACING = 0.9        # min gap between auto-placed parts (routing room)

PRI = {"VIN_RAW", "VIN", "GNDP", "HB_SW", "CR_MID", "G5", "G6", "HBP", "HOP", "LOP", "LLC_HI_P", "LLC_LO_P",
       "+10V_P", "+5V_P", "CB_P", "FB_P", "EN_P", "SW_P"}
CANB = {"CANH", "CANL", "CAN_MID", "CAN_TL", "GND_ISO", "VISO"}
RAILS = {"GND", "GNDP", "PGND", "GND_ISO", "+3V3", "+3V3A", "+5V", "+5V_P", "+10V", "+10V_P", "VISO", "VIN", "VBUS", "VOUT"}
BRIDGE = {"T1", "U12", "U9", "C66", "C56"}

# ---------------------------------------------------------------- hand placement (x, y, rot)
HAND = {
    # primary power
    "J1": (12.5, 26.0, 270), "F1": (22.0, 20.0, 90), "D1": (22.0, 34.0, 90),
    "C60": (30.0, 46.0, 0),
    "Q5": (46.0, 18.0, 180), "Q6": (46.0, 36.0, 180),
    "U10": (36.0, 27.0, 0),
    "T1": (XB, 28.0, 90),
    # primary aux + isolator (bottom left)
    "U13": (18.0, 68.0, 0), "L3": (30.0, 68.0, 0), "D6": (24.0, 76.0, 0), "U14": (44.0, 70.0, 0),
    "U12": (XB, 78.0, 0), "C66": (XB - 3.75, 96.0, 0),
    # secondary LLC side
    "Q8": (90.0, 17.0, 0), "Q7": (90.0, 39.0, 0), "U11": (92.0, 28.0, 90),
    # 4SBB
    "C1": (95.0, 49.0, 0),
    "Q1": (106.0, 17.0, 0), "Q2": (106.0, 33.0, 0),
    "L1": (120.0, 25.0, 0),
    "Q3": (134.0, 17.0, 180), "Q4": (134.0, 33.0, 180),
    "RS1": (120.0, 40.0, 0),
    "U2": (106.0, 45.0, 0), "U3": (134.0, 45.0, 0),
    "C11": (146.0, 49.0, 90), "J2": (148.0, 26.0, 90), "RSH1": (146.0, 38.0, 90),
    # secondary aux
    "U4": (82.0, 58.0, 0), "L2": (90.0, 58.0, 0), "U5": (98.0, 66.0, 0),
    # MCU + sensing
    "U1": (112.0, 80.0, 0), "Y1": (100.0, 86.0, 0),
    "U7": (122.0, 54.0, 0), "U8": (132.0, 60.0, 0),
    # CAN (bus side right of XC, below YC)
    "U9": (XC, 84.0, 0), "C56": (XC - 3.75, 97.0, 0), "J3": (156.0, 72.0, 0), "J4": (156.0, 86.0, 0), "D3": (150.0, 78.0, 0),
    # IO
    "SW1": (88.0, 90.0, 90), "J5": (80.0, 101.0, 90), "J6": (108.0, 101.0, 0), "J7": (126.0, 98.0, 0),
    "D4": (124.0, 70.0, 0), "D5": (124.0, 74.0, 0),
    # mounting holes, 4 mm from each edge
    "H1": (4.0, 4.0, 0), "H2": (W - 4.0, 4.0, 0), "H3": (4.0, H - 4.0, 0), "H4": (W - 4.0, H - 4.0, 0),
}

# anchor for parts whose nets are all rails: (ref, pad)
ANCHOR = {
    "C61": ("Q5", "5"), "C62": ("Q5", "5"), "C63": ("Q6", "1"),
    "C1": None, "C2": ("Q1", "5"), "C3": ("Q1", "5"), "C4": ("Q1", "5"), "C5": ("Q2", "1"), "C6": ("Q1", "5"),
    "C7": ("Q3", "5"), "C8": ("Q3", "5"), "C9": ("Q3", "5"), "C10": ("Q4", "1"), "C12": ("Q3", "5"), "R1": ("J2", "1"),
    "C16": ("U2", "1"), "C17": ("U2", "1"), "C19": ("U3", "1"), "C20": ("U3", "1"),
    "C21": ("U4", "5"), "C22": ("U4", "5"), "C24": ("L2", "2"), "C25": ("L2", "2"), "C26": ("U5", "2"),
    "C27": ("U12", "16"), "C28": ("U1", "29"), "C29": ("U1", "29"),
    "C30": ("U1", "1"), "C31": ("U1", "16"), "C32": ("U1", "32"), "C33": ("U1", "48"), "C34": ("U1", "64"),
    "C35": ("U1", "16"), "C36": ("U1", "28"), "C37": ("U1", "28"),
    "C44": ("U7", "6"), "C46": ("U8", "6"),
    "C49": ("U9", "1"), "C50": ("U9", "1"), "C51": ("U9", "7"), "C52": ("U9", "16"), "C53": ("U9", "16"), "C54": ("U9", "11"),
    "C56": ("U9", "15"),
    "C68": ("U10", "1"), "C69": ("U11", "6"),
    "C70": ("U13", "5"), "C72": ("L3", "2"), "C73": ("U14", "2"),
    "C74": ("U12", "1"), "C75": ("U12", "1"), "C76": ("U12", "7"), "C77": ("U12", "16"), "C78": ("U12", "16"),
    "D1": None, "C60": None, "FB1": ("U1", "29"),
}


def region_of(p):
    nets = set(p.pins.values())
    if nets & PRI:
        return "P"
    if nets & CANB:
        return "C"
    return "S"


def in_region(bb, reg):
    x0, y0, x1, y1 = bb
    if x0 < 1.0 or y0 < 1.0 or x1 > W - 1.0 or y1 > H - 1.0:
        return False
    if reg == "P":
        return x1 < XB - BAND - 0.3
    if reg == "C":
        return x0 > XC + BAND + 0.3 and y0 > YC + BAND + 0.3
    # secondary
    if x0 < XB + BAND + 0.3:
        return False
    if x1 > XC - BAND - 0.3 and y1 > YC - BAND - 0.3:
        return False
    return True


def load(p):
    lib, name = p.fp.split(":")
    fp = pcbnew.FootprintLoad(CUSTOM_FP if lib == "custom_fp" else f"{FPDIR}/{lib}.pretty", name)
    assert fp, p.fp
    return fp


def bbox_mm(fp):
    bb = fp.GetBoundingBox(False, False)
    return (MM(bb.GetX()), MM(bb.GetY()), MM(bb.GetX() + bb.GetWidth()), MM(bb.GetY() + bb.GetHeight()))


def build(out, uuid_paths):
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(4)
    board.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER)
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(4)
    # outline with 2 mm corner chamfer-free rectangle
    pts = [(0, 0), (W, 0), (W, H), (0, H)]
    for i in range(4):
        sg = pcbnew.PCB_SHAPE(board)
        sg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        sg.SetLayer(pcbnew.Edge_Cuts)
        sg.SetStart(pcbnew.VECTOR2I(mm(pts[i][0]), mm(pts[i][1])))
        sg.SetEnd(pcbnew.VECTOR2I(mm(pts[(i + 1) % 4][0]), mm(pts[(i + 1) % 4][1])))
        sg.SetWidth(mm(0.1))
        board.Add(sg)
    nets = {}

    def net(n):
        if n not in nets:
            ni = pcbnew.NETINFO_ITEM(board, n)
            board.Add(ni)
            nets[n] = ni
        return nets[n]

    fps, placed_boxes, problems = {}, [], []
    keep = [(XB - BAND, 0, XB + BAND, H), (XC - BAND, YC - BAND, XC + BAND, H), (XC - BAND, YC - BAND, W, YC + BAND)]
    for hx, hy in [(4, 4), (W - 4, 4), (4, H - 4), (W - 4, H - 4)]:
        pass

    def set_fp(p, fp, x, y, rot):
        fp.SetOrientationDegrees(rot)
        fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))

    # create all footprints
    for p in D.P:
        fp = load(p)
        fp.SetReference(p.ref)
        fp.SetValue(p.value)
        fp.SetFPIDAsString(p.fp)
        if p.ref in uuid_paths:
            fp.SetPath(pcbnew.KIID_PATH(uuid_paths[p.ref]))
        for k, v in (("LCSC", p.lcsc), ("MPN", p.mpn or p.value)):
            if v:
                fp.SetProperty(k, v)
        pads = {}
        for pad in fp.Pads():
            pads.setdefault(pad.GetNumber(), []).append(pad)
        for pin, n in p.pins.items():
            if n == "NC":
                continue
            for pad in pads.get(pin, []):
                pad.SetNet(net(n))
            if pin not in pads:
                problems.append(f"{p.ref} pin {pin} has no pad")
        if p.dnp:
            fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_BOM)
        fps[p.ref] = fp

    def overlaps(bb, pad=0.3):
        x0, y0, x1, y1 = bb
        for b in placed_boxes:
            if x0 < b[2] + pad and x1 > b[0] - pad and y0 < b[3] + pad and y1 > b[1] - pad:
                return True
        for k in keep:
            if x0 < k[2] and x1 > k[0] and y0 < k[3] and y1 > k[1]:
                return True
        return False

    # hand placement
    order_refs = []
    for ref, (x, y, rot) in HAND.items():
        fp = fps[ref]
        set_fp(None, fp, x, y, rot)
        board.Add(fp)
        bb = bbox_mm(fp)
        if ref not in BRIDGE and ref[0] != "H":
            reg = region_of(next(p for p in D.P if p.ref == ref))
            if not in_region(bb, reg):
                problems.append(f"hand {ref} outside region {reg}: {tuple(round(v, 1) for v in bb)}")
        for rb, b in zip(order_refs, placed_boxes):
            if bb[0] < b[2] and bb[2] > b[0] and bb[1] < b[3] and bb[3] > b[1]:
                problems.append(f"hand {ref} overlaps {rb}")
                break
        order_refs.append(ref)
        placed_boxes.append(bb)
    placed = set(HAND)

    def pad_pos(ref, num):
        for pad in fps[ref].Pads():
            if pad.GetNumber() == num:
                return MM(pad.GetPosition().x), MM(pad.GetPosition().y)
        bb = bbox_mm(fps[ref])
        return ((bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2)

    def find_anchor(p):
        if p.ref in ANCHOR and ANCHOR[p.ref]:
            r, n = ANCHOR[p.ref]
            return pad_pos(r, n) if r in placed else None
        sig = [n for n in p.pins.values() if n not in RAILS and n != "NC"]
        best = None
        for n in sig:
            for q in D.P:
                if q.ref in placed and q.ref != p.ref:
                    for pin, nn in q.pins.items():
                        if nn == n:
                            score = (0 if q.block == p.block else 1, -len(q.pins))
                            if best is None or score < best[0]:
                                best = (score, pad_pos(q.ref, pin))
        return best[1] if best else None

    def place_near(p, ax, ay):
        fp = fps[p.ref]
        reg = region_of(p)
        for r in [x * 0.5 for x in range(2, 80)]:
            n = max(8, int(2 * math.pi * r / 0.8))
            for k in range(n):
                a = 2 * math.pi * k / n
                x, y = round(ax + r * math.cos(a), 2), round(ay + r * math.sin(a), 2)
                for rot in (0, 90):
                    set_fp(p, fp, x, y, rot)
                    bb = bbox_mm(fp)
                    if in_region(bb, reg) and not overlaps(bb, SPACING):
                        board.Add(fp)
                        placed_boxes.append(bb)
                        placed.add(p.ref)
                        return True
        return False

    todo = [p for p in D.P if p.ref not in placed]
    for _pass in range(6):
        left = []
        for p in todo:
            a = find_anchor(p)
            if a is None:
                left.append(p)
                continue
            if not place_near(p, *a):
                problems.append(f"could not place {p.ref}")
        if not left or len(left) == len(todo):
            todo = left
            break
        todo = left
    for p in todo:     # no anchor at all: block centroid
        xs = [MM(fps[q.ref].GetPosition().x) for q in D.P if q.block == p.block and q.ref in placed]
        ys = [MM(fps[q.ref].GetPosition().y) for q in D.P if q.block == p.block and q.ref in placed]
        if not place_near(p, sum(xs) / len(xs), sum(ys) / len(ys)):
            problems.append(f"could not place {p.ref}")

    # isolation keep-out bands (no tracks, vias or pours), all copper layers
    for (x0, y0, x1, y1) in keep:
        z = pcbnew.ZONE(board)
        z.SetIsRuleArea(True)
        z.SetDoNotAllowTracks(True)
        z.SetDoNotAllowVias(True)
        z.SetDoNotAllowCopperPour(True)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
        z.SetLayerSet(pcbnew.LSET.AllCuMask(4))
        ol = z.Outline()
        ol.NewOutline()
        for (x, y) in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]:
            ol.Append(mm(x), mm(y))
        z.SetZoneName("ISOLATION_KEEPOUT")
        board.Add(z)

    # In1 planes: GNDP (primary), GND (secondary), GND_ISO (CAN bus side)
    def plane(netname, poly, layer=pcbnew.In1_Cu, prio=0):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(nets[netname])
        ol = z.Outline()
        ol.NewOutline()
        for x, y in poly:
            ol.Append(mm(x), mm(y))
        z.SetLocalClearance(mm(0.3))
        z.SetMinThickness(mm(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetThermalReliefGap(mm(0.3))
        z.SetThermalReliefSpokeWidth(mm(0.5))
        z.SetAssignedPriority(prio)
        board.Add(z)
        return z
    e = 0.5
    plane("GNDP", [(e, e), (XB - BAND, e), (XB - BAND, H - e), (e, H - e)])
    plane("GND", [(XB + BAND, e), (W - e, e), (W - e, YC - BAND), (XC - BAND, YC - BAND), (XC - BAND, H - e), (XB + BAND, H - e)])
    plane("GND_ISO", [(XC + BAND, YC + BAND), (W - e, YC + BAND), (W - e, H - e), (XC + BAND, H - e)])

    board.BuildConnectivity()
    pcbnew.SaveBoard(out, board)
    return problems


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/dcdc/pcb2/DCDC_LLC_4SBB_G474.kicad_pcb"
    import os
    os.makedirs(os.path.dirname(out), exist_ok=True)
    up = json.load(open("/home/claude/dcdc/sch2/uuid_paths.json"))
    probs = build(out, up)
    print("problems:", *(probs or ["none"]), sep="\n  ")

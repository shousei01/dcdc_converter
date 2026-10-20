"""Rev E board builder: every footprint hand-placed from place5.PL (no auto-placement), isolation keep-out bands,
In1 ground planes per domain. Writes an unrouted board and a placement report (overlaps, region violations).
usage: gen_pcb5.py out.kicad_pcb"""
import json, sys
import pcbnew
sys.path.insert(0, "/home/claude/dcdc")
sys.path.insert(0, "/home/claude/dcdc/pcb5")
import design as D
import place5 as P

FPDIR = "/usr/share/kicad/footprints"
CUSTOM_FP = "/home/claude/dcdc/out/custom_fp.pretty"
mm, MM = pcbnew.FromMM, pcbnew.ToMM
W, H = P.W, P.H


def load(p):
    lib, name = p.fp.split(":")
    fp = pcbnew.FootprintLoad(CUSTOM_FP if lib == "custom_fp" else f"{FPDIR}/{lib}.pretty", name)
    assert fp, p.fp
    return fp


def court(fp):
    """courtyard bbox (mm) on the front"""
    try:
        fp.BuildCourtyardCaches()
        poly = fp.GetCourtyard(pcbnew.F_CrtYd)
        bb = poly.BBox()
        if bb.GetWidth() > 0:
            return (MM(bb.GetX()), MM(bb.GetY()), MM(bb.GetX() + bb.GetWidth()), MM(bb.GetY() + bb.GetHeight()))
    except Exception:
        pass
    bb = fp.GetBoundingBox(False, False)
    return (MM(bb.GetX()), MM(bb.GetY()), MM(bb.GetX() + bb.GetWidth()), MM(bb.GetY() + bb.GetHeight()))


def build(out):
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(4)
    board.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER)      # ground planes only, never routed
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(4)
    for i, (a, b) in enumerate([((0, 0), (W, 0)), ((W, 0), (W, H)), ((W, H), (0, H)), ((0, H), (0, 0))]):
        sg = pcbnew.PCB_SHAPE(board)
        sg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        sg.SetLayer(pcbnew.Edge_Cuts)
        sg.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1])))
        sg.SetEnd(pcbnew.VECTOR2I(mm(b[0]), mm(b[1])))
        sg.SetWidth(mm(0.1))
        board.Add(sg)
    nets = {}

    def net(n):
        if n not in nets:
            ni = pcbnew.NETINFO_ITEM(board, n)
            board.Add(ni)
            nets[n] = ni
        return nets[n]

    up = json.load(open(P.UUID_JSON))
    problems, fps = [], {}
    for p in D.P:
        if p.ref not in P.PL:
            problems.append(f"not placed: {p.ref}")
            continue
        fp = load(p)
        fp.SetReference(p.ref)
        fp.SetValue(p.value)
        fp.SetFPIDAsString(p.fp)
        if p.ref in up:
            fp.SetPath(pcbnew.KIID_PATH(up[p.ref]))
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
            fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
        x, y, rot = P.PL[p.ref]
        fp.SetOrientationDegrees(rot)
        fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        board.Add(fp)
        fps[p.ref] = fp
    extra = set(P.PL) - {p.ref for p in D.P}
    if extra:
        problems.append(f"placed but not in design: {sorted(extra)}")

    # overlap + region report (courtyards)
    boxes = {r: court(f) for r, f in fps.items()}
    refs = sorted(boxes)
    for i, a in enumerate(refs):
        A = boxes[a]
        if A[0] < 0.3 or A[1] < 0.3 or A[2] > W - 0.3 or A[3] > H - 0.3:
            problems.append(f"off-board/edge: {a} {tuple(round(v, 1) for v in A)}")
        for b in refs[i + 1:]:
            B = boxes[b]
            if A[0] < B[2] - 0.01 and A[2] > B[0] + 0.01 and A[1] < B[3] - 0.01 and A[3] > B[1] + 0.01:
                if (a, b) not in P.ALLOW_OVERLAP and (b, a) not in P.ALLOW_OVERLAP:
                    problems.append(f"overlap {a} {b}")
    for p in D.P:
        if p.ref in fps and p.ref not in P.BRIDGE and not p.ref.startswith("H"):
            reg = P.region_of(p)
            if not P.in_region(boxes[p.ref], reg):
                problems.append(f"region {reg}: {p.ref} {tuple(round(v, 1) for v in boxes[p.ref])}")

    # isolation keep-out bands (no tracks, vias or pours) on all copper layers
    for (x0, y0, x1, y1) in P.KEEPOUT:
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

    board.BuildConnectivity()
    pcbnew.SaveBoard(out, board)
    return problems


if __name__ == "__main__":
    probs = build(sys.argv[1])
    print(f"{len(probs)} problems")
    for pr in probs:
        print("  ", pr)

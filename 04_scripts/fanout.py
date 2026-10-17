"""Add a fan-out via (0.6/0.3 mm) + short track from every SMD pad on a plane net (GND, GNDP, GND_ISO) to In1.
Usage: fanout.py in.kicad_pcb out.kicad_pcb"""
import math, sys
import pcbnew
sys.path.insert(0, "/home/claude/dcdc")
import gen_pcb2 as GP

mm, MM = pcbnew.FromMM, pcbnew.ToMM
PLANE = {"GND": "S", "GNDP": "P", "GND_ISO": "C"}
VIA_D, VIA_DR, TW, CLR = 0.6, 0.3, 0.4, 0.25


def seg_point_dist(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / L))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def run(src, dst):
    b = pcbnew.LoadBoard(src)
    pads = []
    for fp in b.GetFootprints():
        for pd in fp.Pads():
            bb = pd.GetBoundingBox()
            pads.append((pd, MM(bb.GetX()), MM(bb.GetY()), MM(bb.GetRight()), MM(bb.GetBottom()),
                         pd.GetNetname(), pd.GetAttribute() == pcbnew.PAD_ATTRIB_SMD, fp.GetReference()))
    holes = [(MM(fp.GetPosition().x), MM(fp.GetPosition().y)) for fp in b.GetFootprints() if fp.GetReference().startswith("H")]
    vias, segs = [], []          # (x, y, net) ; (x1,y1,x2,y2,net)
    added = missing = 0

    def box_dist(x, y, x0, y0, x1, y1):
        dx = max(x0 - x, 0, x - x1)
        dy = max(y0 - y, 0, y - y1)
        return math.hypot(dx, dy)

    def ok(vx, vy, px, py, net, own):
        reg = PLANE[net]
        r = VIA_D / 2
        if not GP.in_region((vx - r, vy - r, vx + r, vy + r), reg):
            return False
        for hx, hy in holes:
            if math.hypot(vx - hx, vy - hy) < 3.6 + r:
                return False
        for (pd, x0, y0, x1, y1, n, smd, ref) in pads:
            if pd is own:
                continue
            same = n == net
            if box_dist(vx, vy, x0, y0, x1, y1) < r + (0.15 if same else CLR):
                return False
            # track from pad centre to via must clear other-net pads on F.Cu
            if not same and smd or not same and not smd:
                cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                half = max(x1 - x0, y1 - y0) / 2
                if seg_point_dist(cx, cy, px, py, vx, vy) < half + TW / 2 + CLR and box_dist(cx, cy, min(px, vx), min(py, vy), max(px, vx), max(py, vy)) < half + CLR:
                    return False
        for (x, y, n) in vias:
            if math.hypot(vx - x, vy - y) < VIA_D + (0.15 if n == net else CLR):
                return False
        for (x1, y1, x2, y2, n) in segs:
            if n != net and seg_point_dist(vx, vy, x1, y1, x2, y2) < r + TW / 2 + CLR:
                return False
            if n != net and (seg_point_dist(x1, y1, px, py, vx, vy) < TW + CLR or seg_point_dist(x2, y2, px, py, vx, vy) < TW + CLR):
                return False
        return True

    for (pd, x0, y0, x1, y1, net, smd, ref) in pads:
        if net not in PLANE or not smd:
            continue
        px, py = MM(pd.GetPosition().x), MM(pd.GetPosition().y)
        hw, hh = (x1 - x0) / 2, (y1 - y0) / 2
        placed = False
        for dist in (0.0, 0.25, 0.5, 0.75, 1.0, 1.4, 1.8, 2.4):
            for k in range(16):
                a = 2 * math.pi * k / 16
                ux, uy = math.cos(a), math.sin(a)
                # step out from the pad edge along direction a
                ex = hw * abs(ux) + hh * abs(uy)
                vx = round(px + ux * (ex + VIA_D / 2 + 0.2 + dist), 3)
                vy = round(py + uy * (ex + VIA_D / 2 + 0.2 + dist), 3)
                if ok(vx, vy, px, py, net, pd):
                    via = pcbnew.PCB_VIA(b)
                    via.SetPosition(pcbnew.VECTOR2I(mm(vx), mm(vy)))
                    via.SetWidth(mm(VIA_D)); via.SetDrill(mm(VIA_DR)); via.SetNet(pd.GetNet())
                    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                    b.Add(via)
                    tr = pcbnew.PCB_TRACK(b)
                    tr.SetStart(pd.GetPosition()); tr.SetEnd(pcbnew.VECTOR2I(mm(vx), mm(vy)))
                    tr.SetWidth(mm(TW)); tr.SetLayer(pcbnew.F_Cu); tr.SetNet(pd.GetNet())
                    b.Add(tr)
                    vias.append((vx, vy, net)); segs.append((px, py, vx, vy, net))
                    placed = True
                    added += 1
                    break
            if placed:
                break
        if not placed:
            missing += 1
            print("no fan-out spot for", ref, pd.GetNumber(), net)
    pcbnew.SaveBoard(dst, b)
    print(f"fan-out vias added {added}, failed {missing}")


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])

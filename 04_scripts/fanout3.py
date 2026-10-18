"""Add a fan-out via (0.6/0.3 mm) + short track from every SMD pad on a plane net (GND, GNDP, GND_ISO) to In1.
Usage: fanout.py in.kicad_pcb out.kicad_pcb"""
import math, sys
import pcbnew
sys.path.insert(0, "/home/claude/dcdc")
import gen_pcb3 as GP
NO_FANOUT = {("U7", "4"), ("U8", "4")}

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
    vias, segs = [], []          # (x, y, net, d) ; (x1,y1,x2,y2,net,w,layer)
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            vias.append((MM(t.GetPosition().x), MM(t.GetPosition().y), t.GetNetname(), MM(t.GetWidth())))
        else:
            segs.append((MM(t.GetStart().x), MM(t.GetStart().y), MM(t.GetEnd().x), MM(t.GetEnd().y), t.GetNetname(),
                         MM(t.GetWidth()), t.GetLayer()))
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
        for (x, y, n, d) in vias:
            if math.hypot(vx - x, vy - y) < r + d / 2 + (0.15 if n == net else CLR):
                return False
        for (x1, y1, x2, y2, n, w, L) in segs:
            if n == net:
                continue
            if seg_point_dist(vx, vy, x1, y1, x2, y2) < r + w / 2 + CLR:
                return False
            if L == pcbnew.F_Cu:
                # the F.Cu stub pad->via must clear other-net tracks too (sampled)
                for k in range(0, 11):
                    qx, qy = px + (vx - px) * k / 10, py + (vy - py) * k / 10
                    if seg_point_dist(qx, qy, x1, y1, x2, y2) < TW / 2 + w / 2 + CLR:
                        return False
        return True

    for (pd, x0, y0, x1, y1, net, smd, ref) in pads:
        if net not in PLANE or not smd or (ref, pd.GetNumber()) in NO_FANOUT:
            continue
        want = 3 if (x1 - x0) * (y1 - y0) > 2.0 else 1
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
                    vias.append((vx, vy, net, VIA_D)); segs.append((px, py, vx, vy, net, TW, pcbnew.F_Cu))
                    added += 1
                    want -= 1
                    placed = True
                    if want <= 0:
                        break
            if placed and want <= 0:
                break
        if not placed:
            missing += 1
            print("no fan-out spot for", ref, pd.GetNumber(), net)
    pcbnew.SaveBoard(dst, b)
    print(f"fan-out vias added {added}, failed {missing}")


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])

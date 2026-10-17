"""Grid A* router for the last unconnected items. Layers F.Cu, In2.Cu, B.Cu; vias 0.6/0.3.
Usage: maze.py in.kicad_pcb out.kicad_pcb"""
import heapq, math, re, sys
import numpy as np
from PIL import Image, ImageDraw
import pcbnew
sys.path.insert(0, "/home/claude/dcdc")
from fix_unconnected import drc
import gen_pcb2 as GP

mm, MM = pcbnew.FromMM, pcbnew.ToMM
RES = 20                       # cells per mm (0.05 mm grid)
W, H = int(GP.W * RES), int(GP.H * RES)
TW, CLR, VIA_R = 0.2, 0.205, 0.30
LAYERS = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]


def raster(b):
    """label image per routing layer: net code of copper inflated by clearance + half track width."""
    infl = CLR + TW / 2
    imgs = {L: Image.new("I", (W, H), 0) for L in LAYERS}
    drw = {L: ImageDraw.Draw(imgs[L]) for L in LAYERS}
    P = lambda x, y: (MM(x) * RES, MM(y) * RES)
    for t in b.GetTracks():
        nc = t.GetNetCode() or -1
        if t.Type() == pcbnew.PCB_VIA_T:
            x, y = P(t.GetPosition().x, t.GetPosition().y)
            r = (MM(t.GetWidth()) / 2 + infl + 0.05) * RES
            for L in LAYERS:
                drw[L].ellipse([x - r, y - r, x + r, y + r], fill=nc)
        elif t.GetLayer() in LAYERS:
            x1, y1 = P(t.GetStart().x, t.GetStart().y); x2, y2 = P(t.GetEnd().x, t.GetEnd().y)
            w = (MM(t.GetWidth()) + 2 * infl + 0.1) * RES
            drw[t.GetLayer()].line([x1, y1, x2, y2], fill=nc, width=max(1, int(round(w))))
            r = w / 2
            for (x, y) in ((x1, y1), (x2, y2)):
                drw[t.GetLayer()].ellipse([x - r, y - r, x + r, y + r], fill=nc)
    for fp in b.GetFootprints():
        for pd in fp.Pads():
            nc = pd.GetNetCode() or -1
            bb = pd.GetBoundingBox()
            x0, y0 = P(bb.GetX(), bb.GetY()); x1, y1 = P(bb.GetRight(), bb.GetBottom())
            box = [x0 - infl * RES, y0 - infl * RES, x1 + infl * RES, y1 + infl * RES]
            th = pd.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH)
            for L in LAYERS:
                if th or pd.IsOnLayer(L):
                    drw[L].rectangle(box, fill=nc)
            if pd.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:      # mounting holes: block everything
                for L in LAYERS:
                    drw[L].rectangle(box, fill=-2)
    lab = {L: np.array(imgs[L], dtype=np.int32) for L in LAYERS}
    hole = Image.new("L", (W, H), 0); hd = ImageDraw.Draw(hole)
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            x, y = P(t.GetPosition().x, t.GetPosition().y); r = 0.57 * RES
            hd.ellipse([x - r, y - r, x + r, y + r], fill=1)
    for fp in b.GetFootprints():
        for pd in fp.Pads():
            if pd.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                x, y = P(pd.GetPosition().x, pd.GetPosition().y); r = (MM(pd.GetDrillSize().x) / 2 + 0.45) * RES
                hd.ellipse([x - r, y - r, x + r, y + r], fill=1)
    lab["holes"] = np.array(hole, dtype=bool)
    # keep-out bands and board edge
    for (x0, y0, x1, y1) in [(GP.XB - GP.BAND, 0, GP.XB + GP.BAND, GP.H), (GP.XC - GP.BAND, GP.YC - GP.BAND, GP.XC + GP.BAND, GP.H),
                             (GP.XC - GP.BAND, GP.YC - GP.BAND, GP.W, GP.YC + GP.BAND)]:
        g = TW / 2 + 0.1
        for L in LAYERS:
            lab[L][max(0, int((y0 - g) * RES)):int((y1 + g) * RES) + 1, max(0, int((x0 - g) * RES)):int((x1 + g) * RES) + 1] = -2
    e = int((0.5 + TW / 2) * RES)
    for L in LAYERS:
        lab[L][:e, :] = -2; lab[L][-e:, :] = -2; lab[L][:, :e] = -2; lab[L][:, -e:] = -2
    return lab


def route(lab, nc, a, la, c, lc, plane=False):
    free = {L: (lab[L] == 0) | (lab[L] == nc) for L in LAYERS}
    vr = int(math.ceil((VIA_R + CLR - (CLR + TW / 2)) * RES)) + 1
    # via-ok: free on all layers within radius vr (approx with a square erosion)
    allf = free[LAYERS[0]] & free[LAYERS[1]] & free[LAYERS[2]] & ~lab["holes"]
    viaok = allf.copy()
    for dy in range(-vr, vr + 1):
        for dx in range(-vr, vr + 1):
            if dx * dx + dy * dy <= vr * vr:
                viaok &= np.roll(np.roll(allf, dy, 0), dx, 1)
    ax, ay = int(round(a[0] * RES)), int(round(a[1] * RES))
    cx, cy = int(round(c[0] * RES)), int(round(c[1] * RES))
    li = {L: i for i, L in enumerate(LAYERS)}
    start = (li[la], ay, ax) if la is not None else (0, ay, ax)
    goal_layers = [li[lc]] if lc is not None else [0, 1, 2]
    extra_starts = [] if la is not None else [(1, ay, ax), (2, ay, ax)]
    # open up a small disc around the endpoints on their layers
    for (x, y, L) in ((ax, ay, la), (cx, cy, lc)):
        for LL in ([L] if L is not None else LAYERS):
            free[LL][y, x] = True
    h = lambda y, x: math.hypot(x - cx, y - cy)
    openq = [(h(ay, ax), 0.0, s) for s in [start] + extra_starts]
    came = {s: None for s in [start] + extra_starts}
    gbest = {s: 0.0 for s in [start] + extra_starts}
    nbr = [(-1, 0, 1), (1, 0, 1), (0, -1, 1), (0, 1, 1), (-1, -1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (1, 1, 1.414)]
    exp = 0
    while openq:
        f, g, cur = heapq.heappop(openq)
        l, y, x = cur
        if g > gbest.get(cur, 1e18):
            continue
        if (y == cy and x == cx and l in goal_layers) or (plane and viaok[y, x] and math.hypot(x - ax, y - ay) > 0.9 * RES):
            path = []
            end_plane = plane and not (y == cy and x == cx)
            while cur:
                path.append(cur); cur = came[cur]
            path = path[::-1]
            if end_plane:
                path.append(((path[-1][0] + 1) % 3, path[-1][1], path[-1][2]))   # forces a via at the end
            return path
        exp += 1
        if exp > 8_000_000:
            return None
        L = LAYERS[l]
        for dy, dx, cst in nbr:
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W and free[L][ny, nx]:
                nxt = (l, ny, nx)
                ng = g + cst
                if ng < gbest.get(nxt, 1e18):
                    gbest[nxt] = ng; came[nxt] = cur
                    heapq.heappush(openq, (ng + h(ny, nx), ng, nxt))
        if viaok[y, x]:
            for l2 in range(3):
                if l2 != l:
                    nxt = (l2, y, x)
                    ng = g + 50
                    if ng < gbest.get(nxt, 1e18):
                        gbest[nxt] = ng; came[nxt] = cur
                        heapq.heappush(openq, (ng + h(y, x), ng, nxt))
    return None


def emit(b, path, ni):
    items = []
    seg_start = path[0]
    prev = path[0]
    pdir = None
    def add_seg(p, q):
        if p[1:] == q[1:]:
            return
        tr = pcbnew.PCB_TRACK(b)
        tr.SetStart(pcbnew.VECTOR2I(mm(p[2] / RES), mm(p[1] / RES))); tr.SetEnd(pcbnew.VECTOR2I(mm(q[2] / RES), mm(q[1] / RES)))
        tr.SetWidth(mm(TW)); tr.SetLayer(LAYERS[p[0]]); tr.SetNet(ni); b.Add(tr); items.append(tr)
    for cur in path[1:]:
        if cur[0] != prev[0]:          # via
            add_seg(seg_start, prev)
            v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(mm(cur[2] / RES), mm(cur[1] / RES)))
            v.SetWidth(mm(2 * VIA_R)); v.SetDrill(mm(0.3)); v.SetNet(ni); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            b.Add(v); items.append(v)
            seg_start, pdir = cur, None
        else:
            d = (cur[1] - prev[1], cur[2] - prev[2])
            if pdir is not None and d != pdir:
                add_seg(seg_start, prev); seg_start = prev
            pdir = d
        prev = cur
    add_seg(seg_start, prev)
    return items


def layer_at(b, pt, typ):
    if typ in ("Pad",):
        return pcbnew.F_Cu
    best = None
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            if abs(MM(t.GetPosition().x) - pt[0]) < 0.02 and abs(MM(t.GetPosition().y) - pt[1]) < 0.02:
                return None
        else:
            for q in (t.GetStart(), t.GetEnd()):
                if abs(MM(q.x) - pt[0]) < 0.02 and abs(MM(q.y) - pt[1]) < 0.02 and t.GetLayer() in LAYERS:
                    best = t.GetLayer()
    return best if best is not None else pcbnew.F_Cu


def run(src, dst):
    b = pcbnew.LoadBoard(src)
    filler = pcbnew.ZONE_FILLER(b)
    base, unc = drc(b)
    print("start", base, len(unc))
    for (a, c, net, ta, tc) in unc:
        ni = b.FindNet(net)
        lab = raster(b)
        plane = net in ('GND', 'GNDP', 'GND_ISO')
        if plane and tc == "Pad" and ta != "Pad":
            a, c, ta, tc = c, a, tc, ta
        la, lc = layer_at(b, a, ta), layer_at(b, c, tc)
        print(' ', net, ta, tc, la, lc)
        path = route(lab, ni.GetNetCode(), a, la, c, lc, plane=plane)
        if not path:
            print("NO PATH", net, a, c); continue
        items = emit(b, path, ni)
        filler.Fill(b.Zones())
        bad, _ = drc(b)
        if bad > base:
            print("DRC FAIL", net, bad); [b.Remove(i) for i in items]
        else:
            print("routed", net, a, "->", c, len(items), "items")
    filler.Fill(b.Zones())
    base, unc = drc(b)
    print("end: violations", base, "unconnected", len(unc))
    pcbnew.SaveBoard(dst, b)


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])

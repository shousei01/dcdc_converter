"""Place the Rev E2 series resistors next to J6 and legalise courtyard overlaps by nudging small parts.
Hard: courtyard vs courtyard, pad vs other-net pad (0.2 mm), board edge, isolation keep-out.
Soft: pad vs other-net track/via on the pad's layers (those get ripped and re-routed).
usage: legal.py in.kicad_pcb out.kicad_pcb  -> also writes moves.json"""
import sys, json, math
import pcbnew
from shapely.geometry import box, Point, LineString, Polygon
from shapely.strtree import STRtree
M, mm = pcbnew.ToMM, pcbnew.FromMM
src, dst = sys.argv[1:3]
b = pcbnew.LoadBoard(src)
fps = {f.GetReference(): f for f in b.GetFootprints()}
FIXED = {"T1", "T2", "U1", "U11", "U9", "U12", "J1", "J2", "J3", "J4", "J5", "J6", "J7", "L1", "H1", "H2", "H3", "H4"}

def cy(f):
    s = f.GetCourtyard(pcbnew.F_CrtYd if not f.IsFlipped() else pcbnew.B_CrtYd)
    if s.OutlineCount() == 0:
        bb = f.GetBoundingBox(False, False); return box(M(bb.GetX()), M(bb.GetY()), M(bb.GetRight()), M(bb.GetBottom()))
    o = s.Outline(0); return Polygon([(M(o.CPoint(k).x), M(o.CPoint(k).y)) for k in range(o.PointCount())])

def padgeo(p):
    sh = p.GetEffectivePolygon()
    o = sh.Outline(0); return Polygon([(M(o.CPoint(k).x), M(o.CPoint(k).y)) for k in range(o.PointCount())])

keep = []
for z in b.Zones():
    if z.GetIsRuleArea():
        o = z.Outline().Outline(0); keep.append(Polygon([(M(o.CPoint(k).x), M(o.CPoint(k).y)) for k in range(o.PointCount())]))
edge = box(0.5, 0.5, 159.5, 104.5)
tracks = []
for t in b.GetTracks():
    s, e = t.GetStart(), t.GetEnd()
    if t.Type() == pcbnew.PCB_VIA_T:
        g = Point(M(s.x), M(s.y)).buffer(M(t.GetWidth()) / 2); lay = "all"
    else:
        g = LineString([(M(s.x), M(s.y)), (M(e.x), M(e.y))]).buffer(M(t.GetWidth()) / 2); lay = t.GetLayer()
    tracks.append((g, t.GetNetname(), lay))
ttree = STRtree([g for g, _, _ in tracks])
RIPNETS = {"SWDIO", "SWCLK", "TP_DAC", "TP_GPIO1", "TP_GPIO2", "NRST"}

def state(exclude):
    cys = [(cy(f), r) for r, f in fps.items() if r != exclude]
    pads = [(padgeo(p), p.GetNetname(), r, p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH) for r, f in fps.items() if r != exclude for p in f.Pads()]
    return cys, STRtree([g for g, _ in cys]), pads, STRtree([g for g, *_ in pads])

def cost(f, cys, ctree, pads, ptree):
    c = cy(f)
    if not edge.contains(c): return None
    for i in ctree.query(c):
        if cys[i][0].intersection(c).area > 1e-4: return None
    soft = 0
    for p in f.Pads():
        g = padgeo(p); n = p.GetNetname()
        if any(k.intersects(g) for k in keep): return None
        gb = g.buffer(0.2)
        for i in ptree.query(gb):
            if pads[i][1] != n and pads[i][0].intersects(gb): return None
        for i in ttree.query(gb):
            tg, tn, lay = tracks[i]
            if tn == n or tn in RIPNETS: continue
            if (lay == "all" or lay == pcbnew.F_Cu) and tg.intersects(gb): soft += 1
    return soft

def place(ref, x0, y0, rots, rmax=3.0, step=0.1):
    f = fps[ref]
    cys, ctree, pads, ptree = state(ref)
    best = None
    n = int(rmax / step)
    cands = sorted(((i * step, j * step) for i in range(-n, n + 1) for j in range(-n, n + 1)), key=lambda d: math.hypot(*d))
    for dx, dy in cands:
        d = math.hypot(dx, dy)
        if best and d > best[0]: break
        for rot in rots:
            f.SetOrientationDegrees(rot); f.SetPosition(pcbnew.VECTOR2I(mm(x0 + dx), mm(y0 + dy)))
            c = cost(f, cys, ctree, pads, ptree)
            if c is None: continue
            score = d + 1.5 * c
            if best is None or score < best[0]: best = (score, x0 + dx, y0 + dy, rot, c)
    if best is None:
        raise SystemExit(f"no spot for {ref}")
    _, x, y, rot, c = best
    f.SetOrientationDegrees(rot); f.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    return x, y, rot, c

moves = {}
# --- new series resistors: one above each J6 pad, connector-side pad (2) towards J6
j6 = {p.GetNumber(): p.GetPosition() for p in fps["J6"].Pads()}
for k, r in enumerate(("R123", "R124", "R125", "R126", "R127", "R128", "R129")):
    px = M(j6[str(k + 1)].x); py = M(j6[str(k + 1)].y)
    x, y, rot, c = place(r, px, py - 3.6, (90, 270), rmax=3.0)
    f = fps[r]; p2 = [p for p in f.Pads() if p.GetNumber() == "2"][0]; p1 = [p for p in f.Pads() if p.GetNumber() == "1"][0]
    if M(p2.GetPosition().y) < M(p1.GetPosition().y):      # flip so pad 2 faces J6
        f.SetOrientationDegrees((rot + 180) % 360)
        if cost(f, *state(r)) is None: f.SetOrientationDegrees(rot)
    moves[r] = ("new", round(x, 2), round(y, 2), f.GetOrientationDegrees(), c)
    print(r, moves[r])

# --- courtyard legalisation: move the smaller part of every overlapping pair, smallest moves first
def overlaps():
    out = []
    items = list(fps.items())
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            (ra, fa), (rb, fb) = items[i], items[j]
            if fa.IsFlipped() != fb.IsFlipped(): continue
            if cy(fa).intersection(cy(fb)).area > 1e-4: out.append((ra, rb))
    return out

# flyback cluster next to T2: planned shifts (Q11 below the T2 courtyard, D8 clear of T2, R116 / C94 above D8)
PRE = {"D8": (-0.3, 0), "Q11": (0, 1.7), "R114": (0, 2.0), "C94": (0, -0.65), "R116": (0, -1.45)}
for r, (dx, dy) in PRE.items():
    f = fps[r]; x0, y0 = M(f.GetPosition().x), M(f.GetPosition().y)
    f.SetPosition(pcbnew.VECTOR2I(mm(x0 + dx), mm(y0 + dy)))
    moves[r] = ("move", dx, dy, f.GetOrientationDegrees(), -1, round(x0, 3), round(y0, 3))
for it in range(20):
    ov = overlaps()
    if not ov: break
    ra, rb = ov[0]
    area = lambda r: cy(fps[r]).area
    mv = rb if (ra in FIXED or (rb not in FIXED and area(rb) <= area(ra))) else ra
    if mv in FIXED: raise SystemExit(f"both fixed {ra} {rb}")
    f = fps[mv]; x0, y0 = M(f.GetPosition().x), M(f.GetPosition().y); rot0 = f.GetOrientationDegrees()
    x, y, rot, c = place(mv, x0, y0, (rot0,), rmax=3.0, step=0.05)
    if mv in moves and moves[mv][0] == "move":
        ox, oy = moves[mv][5], moves[mv][6]
    else:
        ox, oy = x0, y0
    moves[mv] = ("move", round(x - ox, 2), round(y - oy, 2), rot, c, ox, oy)
    print("move", mv, "for", ra, rb, moves[mv])
print("remaining overlaps", overlaps())
pcbnew.SaveBoard(dst, b)
json.dump(moves, open(dst.replace(".kicad_pcb", "_moves.json"), "w"), indent=1)

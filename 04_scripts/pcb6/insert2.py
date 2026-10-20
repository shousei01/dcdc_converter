"""Rev E2: insert R123..R129 into the existing debug / +3V3 routing (hand-designed geometry).
usage: insert2.py in.kicad_pcb out.kicad_pcb"""
import sys, math
import pcbnew
M, mm = pcbnew.ToMM, pcbnew.FromMM
src, dst = sys.argv[1:3]
b = pcbnew.LoadBoard(src)
fps = {f.GetReference(): f for f in b.GetFootprints()}
F, I2, BC = pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu
LN = {"F": F, "2": I2, "B": BC}
V = lambda p: pcbnew.VECTOR2I(mm(p[0]), mm(p[1]))
P = lambda v: (M(v.x), M(v.y))
close = lambda p, q, t=0.003: math.dist(p, q) < t

DEL = []
TR = list(b.GetTracks())
def find(layer, net, a, c):
    out = [t for t in TR if t not in DEL and t.Type() == pcbnew.PCB_TRACE_T and t.GetLayer() == LN[layer] and t.GetNetname() == net
           and ((close(P(t.GetStart()), a) and close(P(t.GetEnd()), c)) or (close(P(t.GetStart()), c) and close(P(t.GetEnd()), a)))]
    assert len(out) == 1, (layer, net, a, c, len(out))
    return out[0]
def rm(layer, net, a, c): DEL.append(find(layer, net, a, c))
def move_end(layer, net, a, c, old, new):
    t = find(layer, net, a, c)
    if close(P(t.GetStart()), old): t.SetStart(V(new))
    else: t.SetEnd(V(new))
def trk(layer, net, *pts, w=0.2):
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(V(a)); t.SetEnd(V(c)); t.SetLayer(LN[layer]); t.SetWidth(mm(w))
        t.SetNet(b.FindNet(net)); b.Add(t); TR.append(t)
def via(p, net):
    v = pcbnew.PCB_VIA(b); v.SetPosition(V(p)); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3))
    v.SetLayerPair(F, BC); v.SetNet(b.FindNet(net)); b.Add(v); TR.append(v)
def findvia(p):
    out = [t for t in TR if t.Type() == pcbnew.PCB_VIA_T and close(P(t.GetPosition()), p)]
    assert len(out) == 1, p
    return out[0]
def place(ref, c, ang, first="top"):
    f = fps[ref]; f.SetPosition(V(c)); f.SetOrientationDegrees(ang)
    p1 = [P(p.GetPosition()) for p in f.Pads() if p.GetNumber() == "1"][0]
    ok = {"top": p1[1] < c[1] - 0.1, "bottom": p1[1] > c[1] + 0.1, "left": p1[0] < c[0] - 0.1, "right": p1[0] > c[0] + 0.1}[first]
    if not ok: f.SetOrientationDegrees(ang + 180)
    return {p.GetNumber(): tuple(round(v, 4) for v in P(p.GetPosition())) for p in f.Pads()}

# ---------------- SWDIO / R123: trunk -> new via V1' -> R123 -> old junction via V1 (now SWDIO_C) ----------------
p = place("R123", (101.0, 98.75), 0, "right")          # pad1 (MCU) right, pad2 (connector) left
rm("2", "SWDIO", (99.886, 99.476), (100.053, 99.309))
move_end("2", "SWDIO", (100.053, 99.309), (100.053, 86.485), (100.053, 99.309), (100.053, 97.5))
trk("2", "SWDIO", (100.053, 97.5), (101.303, 98.75), (102.15, 98.75))
via((102.15, 98.75), "SWDIO")
trk("F", "SWDIO", (102.15, 98.75), p["1"])
trk("F", "SWDIO_C", p["2"], (p["2"][0], 98.872), (99.886, 99.476))
# J7 branch on B.Cu now leaves V1 downwards, runs under J6 and rejoins the old y=95.336 run near J7
rm("B", "SWDIO", (104.026, 95.336), (99.886, 99.476))
move_end("B", "SWDIO", (125.791, 95.336), (104.026, 95.336), (104.026, 95.336), (124.664, 95.336))
trk("B", "SWDIO_C", (99.886, 99.476), (101.41, 101.0), (119.0, 101.0), (124.664, 95.336))

# ---------------- SWCLK / R124: via-R-via on the In2 trunk ----------------
p = place("R124", (106.3, 96.65), 90, "top")
rm("2", "SWCLK", (105.609, 95.823), (105.609, 91.091)); trk("2", "SWCLK", (105.609, 91.091), (105.609, 95.54))
for a, c in (((105.937, 96.151), (105.609, 95.823)), ((105.937, 96.774), (105.937, 96.151)), ((105.496, 97.214), (105.937, 96.774)),
             ((105.191, 97.214), (105.496, 97.214)), ((102.668, 99.737), (105.191, 97.214)), ((102.668, 99.88), (102.668, 99.737))):
    rm("2", "SWCLK", a, c)
via((105.609, 95.54), "SWCLK")
trk("F", "SWCLK", (105.609, 95.54), (106.3, 96.231), p["1"])
trk("F", "SWCLK_C", p["2"], (106.3, 97.9))
via((106.3, 97.9), "SWCLK_C")
trk("2", "SWCLK_C", (106.3, 97.9), (106.3, 98.6), (105.02, 99.88), (102.668, 99.88))

# ---------------- TP_DAC / R125: via-R-via beside the x=116.511 In2 run ----------------
p = place("R125", (117.4, 94.3), 90, "top")
rm("2", "TP_DAC", (116.511, 90.103), (116.511, 95.665)); trk("2", "TP_DAC", (116.511, 90.103), (116.511, 93.79))
via((116.511, 93.79), "TP_DAC")
trk("F", "TP_DAC", (116.511, 93.79), p["1"])
trk("F", "TP_DAC_C", p["2"], (116.96, 95.25), (116.65, 95.25))
via((116.65, 95.25), "TP_DAC_C")
trk("2", "TP_DAC_C", (116.65, 95.25), (116.511, 95.389), (116.511, 95.665))

# ---------------- TP_GPIO1 / R126: via-R-via, R126 ends on the old via (110.205, 97.768) ----------------
p = place("R126", (110.205, 96.65), 90, "top")
rm("2", "TP_GPIO1", (110.205, 86.206), (110.205, 97.768)); trk("2", "TP_GPIO1", (110.205, 86.206), (110.205, 95.54))
via((110.205, 95.54), "TP_GPIO1")
trk("F", "TP_GPIO1", (110.205, 95.54), p["1"])
trk("F", "TP_GPIO1_C", p["2"], (110.205, 97.768))
DEL.append(findvia((110.205, 97.768)))                 # was the In2 -> F.Cu transition; now F.Cu only

# ---------------- TP_GPIO2 / R127: trunk jogs to x=108.6 for via-R-via ----------------
p = place("R127", (108.6, 96.65), 90, "top")
rm("2", "TP_GPIO2", (109.594, 86.212), (109.594, 99.198))
trk("2", "TP_GPIO2", (109.594, 86.212), (109.594, 94.546), (108.6, 95.54))
via((108.6, 95.54), "TP_GPIO2")
trk("F", "TP_GPIO2", (108.6, 95.54), p["1"])
trk("F", "TP_GPIO2_C", p["2"], (108.6, 97.75))
via((108.6, 97.75), "TP_GPIO2_C")
trk("2", "TP_GPIO2_C", (108.6, 97.75), (109.594, 98.744), (109.594, 99.198))

# ---------------- NRST / R128: horizontal right of the NRST via, then into J6.6 ----------------
p = place("R128", (113.0, 98.62), 0, "left")
rm("F", "NRST", (111.81, 98.623), (111.81, 101.0))
trk("F", "NRST", (111.81, 98.623), p["1"])
trk("F", "NRST_C", p["2"], (p["2"][0], 99.3), (112.51, 100.3))

# ---------------- +3V3 / R129: in the x=122.523 riser, C51 trunk re-joined above it ----------------
p = place("R129", (122.523, 92.7), 90, "top")
move_end("F", "+3V3", (122.523, 95.46), (122.523, 91.698), (122.523, 95.46), p["1"])
trk("F", "PROG_3V3", p["2"], (122.523, 95.46), w=0.25)
rm("F", "+3V3", (125.577, 95.46), (124.05, 95.46))
rm("F", "+3V3", (125.577, 93.873), (125.577, 95.46))
rm("F", "+3V3", (130.6, 88.85), (125.577, 93.873))
trk("F", "+3V3", (122.523, 91.698), (127.752, 91.698), (130.6, 88.85), w=0.25)

# ---------------- re-net the connector side by copper flood from the connector pads ----------------
for t in DEL: b.Remove(t)
TR = [t for t in TR if t not in DEL]
def items_of(nets):
    return [t for t in TR if t.GetNetname() in nets]
def ends(t):
    return [P(t.GetPosition())] if t.Type() == pcbnew.PCB_VIA_T else [P(t.GetStart()), P(t.GetEnd())]
def touches(t, u):
    if t.Type() == pcbnew.PCB_VIA_T and u.Type() == pcbnew.PCB_VIA_T: return close(P(t.GetPosition()), P(u.GetPosition()))
    if t.Type() != pcbnew.PCB_VIA_T and u.Type() != pcbnew.PCB_VIA_T and t.GetLayer() != u.GetLayer(): return False
    return any(close(x, y, 0.01) for x in ends(t) for y in ends(u))
def in_pad(t, pad):
    if t.Type() != pcbnew.PCB_VIA_T and not pad.IsOnLayer(t.GetLayer()): return False
    return any(pad.HitTest(V(e)) for e in ends(t))
newnet = {"SWDIO": "SWDIO_C", "SWCLK": "SWCLK_C", "TP_DAC": "TP_DAC_C", "TP_GPIO1": "TP_GPIO1_C", "TP_GPIO2": "TP_GPIO2_C",
          "NRST": "NRST_C", "+3V3": "PROG_3V3"}
for old, new in newnet.items():
    its = items_of({old, new})
    cpads = [pd for f in b.GetFootprints() for pd in f.Pads() if pd.GetNetname() == new]
    mpads = [(f.GetReference(), pd.GetNumber()) for f in b.GetFootprints() for pd in f.Pads() if pd.GetNetname() == old]
    seen = set(); stack = [t for t in its if any(in_pad(t, pd) for pd in cpads)]
    while stack:
        t = stack.pop()
        if id(t) in seen: continue
        seen.add(id(t))
        stack += [u for u in its if id(u) not in seen and touches(t, u)]
    got = [t for t in its if id(t) in seen]
    bad = [(r, n) for f in b.GetFootprints() for pd in f.Pads() if pd.GetNetname() == old
           for r, n in [(f.GetReference(), pd.GetNumber())] if any(in_pad(t, pd) for t in got)]
    for t in got: t.SetNet(b.FindNet(new))
    print(f"{old:9s} -> {new:10s}: {len(got)} items re-netted; connector-side copper touching {old} pads: {bad}")
pcbnew.SaveBoard(dst, b)

"""Re-attach copper of parts moved by legal.py (courtyard fixes) - hand-designed geometry.
usage: fix_moves.py in.kicad_pcb out.kicad_pcb"""
import sys, math, json
import pcbnew
M, mm = pcbnew.ToMM, pcbnew.FromMM
src, dst = sys.argv[1:3]
b = pcbnew.LoadBoard(src)
orig = pcbnew.LoadBoard("/home/claude/dcdc/pcb5/DCDC_LLC_4SBB_G474_revE_preE2.kicad_pcb")
F, BC = pcbnew.F_Cu, pcbnew.B_Cu
LN = {"F": F, "B": BC}
V = lambda p: pcbnew.VECTOR2I(mm(p[0]), mm(p[1]))
P = lambda v: (M(v.x), M(v.y))
close = lambda p, q, t=0.003: math.dist(p, q) < t
TR = list(b.GetTracks()); DEL = []
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
fp = lambda r: b.FindFootprintByReference(r)
def pad(r, n): return tuple(round(v, 4) for v in P([p for p in fp(r).Pads() if p.GetNumber() == n][0].GetPosition()))

# ---- simple drags (tiny moves): shift track ends that sat on the old pad
for r in ("C98", "C69", "C34"):
    fo, fn = orig.FindFootprintByReference(r), fp(r)
    d = (M(fn.GetPosition().x - fo.GetPosition().x), M(fn.GetPosition().y - fo.GetPosition().y))
    for po in fo.Pads():
        for t in TR:
            if t.Type() != pcbnew.PCB_TRACE_T or not po.IsOnLayer(t.GetLayer()) or t.GetNetname() != po.GetNetname(): continue
            for getter, setter in ((t.GetStart, t.SetStart), (t.GetEnd, t.SetEnd)):
                e = getter()
                if po.HitTest(e): setter(V((M(e.x) + d[0], M(e.y) + d[1])))
    print("dragged", r, d)

# ---- flyback stage (Q11 / R114 / D8 / C94 / R116)
fp("R114").SetPosition(V((63.5, 68.5)))
s, r1 = pad("Q11", "2"), pad("R114", "1")
rm("F", "FLY_SRC", (61.55, 67.338), (61.55, 65.838))
rm("F", "FLY_SRC", (61.55, 67.338), (57.008, 71.879))
y_join = round(r1[1] + (r1[0] - 57.008), 3)                       # 45 deg from the shunt pad down to x = 57.008
move_end("F", "FLY_SRC", (57.008, 71.879), (57.008, 75.433), (57.008, 71.879), (57.008, y_join))
trk("F", "FLY_SRC", s, (s[0] + (s[1] - r1[1]), r1[1]), r1, w=0.6)  # source -> shunt (power)
trk("F", "FLY_SRC", r1, (57.008, y_join), w=0.6)                   # shunt -> current-sense filter (Kelvin from the shunt pad)
g = pad("Q11", "1")
trk("F", "FLY_G", (59.65, 65.838), g, w=0.4)
d = pad("Q11", "3")
trk("F", "FLY_DRN", d, (d[0], 64.2), w=0.6)
for a, c in (((53.4, 60.862), (54.712, 60.862)), ((54.538, 62.0), (53.4, 60.862)), ((54.712, 60.862), (55.4, 60.175)), ((55.4, 62.0), (54.538, 62.0))):
    rm("F", "FLY_CLP", a, c)
c1, r16, d1 = pad("C94", "1"), pad("R116", "1"), pad("D8", "1")
trk("F", "FLY_CLP", r16, (c1[0], r16[1]), w=0.6)
trk("F", "FLY_CLP", (c1[0], r16[1]), (c1[0], d1[1]), w=0.6)
c2 = pad("C94", "2")
rm("F", "VIN", (55.4, 58.565), (55.4, 58.625))
rm("F", "VIN", (54.335, 57.5), (55.4, 58.565))
trk("F", "VIN", (54.335, 57.5), (54.335 + (c2[1] - 57.5), c2[1]), c2, w=0.6)

# ---- R64 (gate pull-down of Q5), moved off the T1 courtyard
p1, p2 = pad("R64", "1"), pad("R64", "2")
t = find("F", "G5", (53.9, 31.0), (55.09, 31.4)); t.SetLocked(False); DEL.append(t)
trk("F", "G5", (53.9, 31.0), (p1[0], 31.0 - (53.9 - p1[0])), p1, w=0.3)
trk("F", "HB_SW", p2, (55.0, p2[1] + (55.0 - p2[0])), (55.0, 32.9), w=0.3)

# ---- R113 0.3 mm left: keeps Q11's pin-1 silk marker off its pad
fp("R113").SetPosition(V((58.1, M(fp("R113").GetPosition().y))))
move_end("F", "FLY_G", (58.4, 65.838), (58.4, 66.69), (58.4, 65.838), (58.1, 65.838))
move_end("F", "FLY_G", (58.1, 65.838), (58.4, 66.69), (58.4, 66.69), (58.1, 66.69))

# ---- library ids of the Rev E2 resistors
for r in ("R123", "R124", "R125", "R126", "R127", "R128"): fp(r).SetFPID(pcbnew.LIB_ID("Resistor_SMD", "R_0402_1005Metric"))
fp("R129").SetFPID(pcbnew.LIB_ID("Resistor_SMD", "R_0603_1608Metric"))

for t in DEL: b.Remove(t)
pcbnew.SaveBoard(dst, b)
print("ok")

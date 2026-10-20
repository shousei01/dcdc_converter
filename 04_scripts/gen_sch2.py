"""Wired, multi-sheet schematic generator (KiCad 6 format) for EasyEDA Pro import.

- One A3 sheet per functional block (hierarchical; root sheet holds the sheet symbols).
- Rails and grounds use power symbols; signals inside a sheet are drawn as wires (MST + L/Z routing
  with collision checks); a net that leaves the sheet gets ONE global label; a wire that cannot be
  routed cleanly falls back to a pair of local labels.
"""
import copy, json, math, sys, uuid as uuidlib
from kiutils.schematic import Schematic
from kiutils.symbol import SymbolLib
from kiutils.items.common import Position, Property, Effects, Font, Justify, Stroke, PageSettings, TitleBlock
from kiutils.items.schitems import (SchematicSymbol, LocalLabel, GlobalLabel, Connection, NoConnect, Junction, Text,
                                    HierarchicalSheet, HierarchicalSheetInstance, SymbolInstance)

sys.path.insert(0, "/home/claude/dcdc")
import design as D
import gen_sch as G0
from sch_place import SHEETS, PLACE, FIELDS, NOTES, NOWIRE

G = 2.54
STUB = 2.54
uid = lambda: str(uuidlib.uuid4())
GROUNDS = {"GND", "GNDP", "PGND", "GND_ISO"}
RAILS = {"+3V3", "+3V3A", "+5V", "+5V_P", "+10V", "+10V_P", "VISO", "VIN", "VBUS", "VOUT"}
PROJECT = "DCDC_LLC_4SBB_G474"


def sn(v):
    return round(round(v / 1.27) * 1.27, 3)


def hid():
    return Effects(font=Font(height=1.27, width=1.27), hide=True)


def fnt(sz=1.27, just=None, bold=False):
    return Effects(font=Font(height=sz, width=sz, bold=bold), justify=Justify(horizontally=just) if just else Justify())


# ------------------------------------------------------------------ geometry with mirror
def lib_xform(x, y, rot, mirror):
    if mirror:
        x = -x
    r = math.radians(rot)
    X = x * math.cos(r) - y * math.sin(r)
    Y = x * math.sin(r) + y * math.cos(r)
    return X, -Y


def pin_geom(p, sx, sy, rot, mirror):
    dx, dy = lib_xform(p.position.X, p.position.Y, rot, mirror)
    a = p.position.angle
    if mirror:
        a = (180 - a) % 360
    a = (a + 180 + rot) % 360
    vx, vy = round(math.cos(math.radians(a))), -round(math.sin(math.radians(a)))
    return (sn(sx + dx), sn(sy + dy)), (vx, vy)


def body_box(sym, sx, sy, rot, mirror):
    pts = []
    for u in sym.units:
        for gi in getattr(u, "graphicItems", []):
            for attr in ("start", "end", "center", "mid"):
                q = getattr(gi, attr, None)
                if q is not None and hasattr(q, "X"):
                    pts.append((q.X, q.Y))
            if hasattr(gi, "radius") and getattr(gi, "center", None) is not None:
                r = gi.radius
                pts += [(gi.center.X - r, gi.center.Y - r), (gi.center.X + r, gi.center.Y + r)]
            for q in getattr(gi, "points", []) or []:
                pts.append((q.X, q.Y))
    if not pts:
        return None
    tp = [lib_xform(x, y, rot, mirror) for x, y in pts]
    xs, ys = [sx + a for a, b in tp], [sy + b for a, b in tp]
    return (min(xs), min(ys), max(xs), max(ys))


# ------------------------------------------------------------------ power symbols
_pwr_cache = {}


def power_symbol(net):
    if net in _pwr_cache:
        return _pwr_cache[net]
    base = G0.load_lib_symbol("power:GND" if net in GROUNDS else "power:+3V3")
    s = copy.deepcopy(base)
    s.libraryNickname, s.entryName = "pwr", net
    for u in s.units:
        u.entryName = net
        for p in u.pins:
            p.name = net
    for pr in s.properties:
        if pr.key == "Value":
            pr.value = net
        if pr.key in ("ki_description",):
            pr.value = f"Power symbol for net {net}"
    _pwr_cache[net] = s
    return s


# ------------------------------------------------------------------ router state
class Sheet:
    def __init__(self, name):
        self.name = name
        self.segs = []          # (x1,y1,x2,y2,net)
        self.points = {}        # (x,y) -> net   (pin ends, stub ends, label/flag anchors)
        self.boxes = []         # body boxes (shrunk)
        self.labels, self.glabels, self.wires, self.juncs, self.ncs, self.syms, self.texts = [], [], [], [], [], [], []
        self.fallbacks = []

    # --- collision helpers
    @staticmethod
    def on_seg(px, py, s):
        x1, y1, x2, y2 = s[:4]
        if x1 == x2 == px:
            return min(y1, y2) - 1e-6 <= py <= max(y1, y2) + 1e-6
        if y1 == y2 == py:
            return min(x1, x2) - 1e-6 <= px <= max(x1, x2) + 1e-6
        return False

    @staticmethod
    def overlap(a, b):
        ax1, ay1, ax2, ay2 = a[:4]
        bx1, by1, bx2, by2 = b[:4]
        if ax1 == ax2 == bx1 == bx2:
            lo, hi = max(min(ay1, ay2), min(by1, by2)), min(max(ay1, ay2), max(by1, by2))
            return hi - lo > 1e-6
        if ay1 == ay2 == by1 == by2:
            lo, hi = max(min(ax1, ax2), min(bx1, bx2)), min(max(ax1, ax2), max(bx1, bx2))
            return hi - lo > 1e-6
        return False

    def seg_ok(self, s, net, ignore_box=None):
        x1, y1, x2, y2 = s
        if (x1, y1) == (x2, y2):
            return True
        for t in self.segs:
            if t[4] == net:
                continue
            if self.overlap(s, t):
                return False
            if self.on_seg(t[0], t[1], s) or self.on_seg(t[2], t[3], s):
                return False
            if self.on_seg(x1, y1, t) or self.on_seg(x2, y2, t):
                return False
        for (px, py), n in self.points.items():
            if n != net and self.on_seg(px, py, s):
                return False
        for i, b in enumerate(self.boxes):
            if i == ignore_box:
                continue
            bx1, by1, bx2, by2 = b
            if x1 == x2:
                if bx1 < x1 < bx2 and max(y1, y2) > by1 and min(y1, y2) < by2:
                    return False
            else:
                if by1 < y1 < by2 and max(x1, x2) > bx1 and min(x1, x2) < bx2:
                    return False
        return True

    def add_seg(self, s, net):
        x1, y1, x2, y2 = s
        if (x1, y1) == (x2, y2):
            return
        self.segs.append((x1, y1, x2, y2, net))
        self.wires.append(Connection(type="wire", points=[Position(x1, y1), Position(x2, y2)],
                                     stroke=Stroke(width=0, type="default"), uuid=uid()))

    def route(self, a, b, net):
        (ax, ay), (bx, by) = a, b
        cands = []
        if ax == bx or ay == by:
            cands.append([(ax, ay, bx, by)])
        cands.append([(ax, ay, bx, ay), (bx, ay, bx, by)])
        cands.append([(ax, ay, ax, by), (ax, by, bx, by)])
        for off in [k * G for k in range(1, 9)] + [-k * G for k in range(1, 9)]:
            mx = sn((ax + bx) / 2 + off)
            cands.append([(ax, ay, mx, ay), (mx, ay, mx, by), (mx, by, bx, by)])
            my = sn((ay + by) / 2 + off)
            cands.append([(ax, ay, ax, my), (ax, my, bx, my), (bx, my, bx, by)])
        for c in cands:
            c = [s for s in c if (s[0], s[1]) != (s[2], s[3])]
            if all(self.seg_ok(s, net) for s in c):
                for s in c:
                    self.add_seg(s, net)
                    for p in ((s[0], s[1]), (s[2], s[3])):
                        self.points.setdefault(p, net)
                return True
        return False



# ------------------------------------------------------------------ text collision helpers
def tbox(cx, cy, txt, h, vertical=False):
    lines = txt.split("\n")
    w = max(len(l) for l in lines) * 0.92 * h + 0.3
    hh = (1.6 * h) * len(lines)
    if vertical:
        w, hh = hh, w
    return (cx - w / 2, cy - hh / 2, cx + w / 2, cy + hh / 2)


def ov(a, b):
    dx = min(a[2], b[2]) - max(a[0], b[0])
    dy = min(a[3], b[3]) - max(a[1], b[1])
    return dx * dy if dx > 0 and dy > 0 else 0.0


def label_box(pt, ang, txt, h, glob):
    n = len(txt) * 0.92 * h + (2.6 if glob else 0.4)
    t = 1.5 * h
    x, y = pt
    return {0: (x, y - t / 2, x + n, y + t / 2), 180: (x - n, y - t / 2, x, y + t / 2),
            90: (x - t / 2, y - n, x + t / 2, y), 270: (x - t / 2, y, x + t / 2, y + n)}[ang]

# ------------------------------------------------------------------ build one sheet
def build_sheet(sheet_name, blocks, net_sheets, refs_out):
    sh = Sheet(sheet_name)
    sh.tobst = []
    sh.pwr = []
    full_boxes = []
    pin_lines = []
    parts = [p for p in D.P if p.block in blocks]
    placed = []
    libsyms = {}
    for p in parts:
        if p.ref not in PLACE:
            raise SystemExit(f"no placement for {p.ref}")
        x, y, rot, *rest = PLACE[p.ref]
        mirror = bool(rest and rest[0])
        x, y = sn(x), sn(y)
        sym = G0.get_symbol(p.sym)
        libsyms[p.sym] = sym
        placed.append((p, sym, x, y, rot, mirror))
        bb = body_box(sym, x, y, rot, mirror)
        if bb:
            full_boxes.append(bb)
            sh.boxes.append((bb[0] + 0.3, bb[1] + 0.3, bb[2] - 0.3, bb[3] - 0.3))

    # pins, stubs
    net_ends = {}       # net -> list of stub-end points
    endpc = {}
    for p, sym, x, y, rot, mirror in placed:
        groups = {}
        for sp in G0.all_pins(sym):
            pt, v = pin_geom(sp, x, y, rot, mirror)
            groups.setdefault(pt, []).append((sp, v))
            L = sp.length or 0
            ex, ey = pt[0] - v[0] * L, pt[1] - v[1] * L
            pin_lines.append((min(pt[0], ex) - 0.2, min(pt[1], ey) - 0.2, max(pt[0], ex) + 0.2, max(pt[1], ey) + 0.2))
        for pt, lst in groups.items():
            nets = {p.pins.get(sp.number) for sp, _ in lst} - {None}
            if len(nets) > 1:
                raise SystemExit(f"{p.ref}: stacked pins on different nets {nets}")
            if not nets or nets == {"NC"}:
                sh.ncs.append(NoConnect(position=Position(*pt), uuid=uid()))
                sh.points[pt] = "~NC~" + p.ref
                continue
            net = nets.pop()
            v = lst[0][1]
            end = (sn(pt[0] + v[0] * STUB), sn(pt[1] + v[1] * STUB))
            sh.points[pt] = net
            sh.points[end] = net
            sh.segs.append((pt[0], pt[1], end[0], end[1], net))
            sh.wires.append(Connection(type="wire", points=[Position(*pt), Position(*end)],
                                       stroke=Stroke(width=0, type="default"), uuid=uid()))
            if (p.ref, lst[0][0].number) in NOWIRE:
                sh.__dict__.setdefault('nowire', []).append((end, v, net))
                continue
            net_ends.setdefault(net, []).append((end, v))
            endpc[end] = len(G0.all_pins(sym))

    # power symbols at every rail/ground stub
    pwr_i = [0]

    def put_power(net, pt, v):
        s = power_symbol(net)
        libsyms["pwr:" + net] = s
        if net in GROUNDS:
            rot = {(0, 1): 0, (0, -1): 180, (1, 0): 90, (-1, 0): 270}[v]
        else:
            rot = {(0, -1): 0, (0, 1): 180, (-1, 0): 90, (1, 0): 270}[v]
        pwr_i[0] += 1
        ref = f"#PWR{sheet_name[:3].upper()}{pwr_i[0]:03d}"
        ss = SchematicSymbol(libraryNickname="pwr", entryName=net, position=Position(pt[0], pt[1], rot), unit=1,
                             inBom=False, onBoard=True, uuid=uid())
        vx, vy = v
        body = (min(pt[0], pt[0] + vx * 2.8) - (1.4 if vy else 0), min(pt[1], pt[1] + vy * 2.8) - (1.4 if vx else 0),
                max(pt[0], pt[0] + vx * 2.8) + (1.4 if vy else 0), max(pt[1], pt[1] + vy * 2.8) + (1.4 if vx else 0))
        sh.tobst.append(body)
        fang = rot if rot in (90, 270) else 0
        cpos = pt
        ss.properties = [
            Property(key="Reference", value=ref, id=0, position=Position(pt[0], pt[1], 0), effects=hid()),
            Property(key="Value", value=net, id=1, position=Position(pt[0], pt[1], fang), effects=fnt(1.0)),
            Property(key="Footprint", value="", id=2, position=Position(pt[0], pt[1], 0), effects=hid()),
            Property(key="Datasheet", value="", id=3, position=Position(pt[0], pt[1], 0), effects=hid()),
        ]
        ss.pins = {"1": uid()}
        sh.syms.append(ss)
        sh.pwr.append((ss, net, pt, v, body))
        refs_out.append((ss.uuid, ref, net, ""))

    for net, ends in net_ends.items():
        if net in GROUNDS or net in RAILS:
            groups = {}
            for pt, v in ends:
                key = (v, pt[1] if v[1] else pt[0])
                groups.setdefault(key, []).append(pt)
            for (v, _), pts in groups.items():
                axis = 0 if v[1] else 1
                pts.sort(key=lambda q: q[axis])
                runs, cur = [], [pts[0]]
                for q in pts[1:]:
                    if abs(q[axis] - cur[-1][axis] - G) < 1e-3 and sh.seg_ok((cur[-1][0], cur[-1][1], q[0], q[1]), net):
                        cur.append(q)
                    else:
                        runs.append(cur); cur = [q]
                runs.append(cur)
                for run in runs:
                    for p0, p1 in zip(run, run[1:]):
                        sh.add_seg((p0[0], p0[1], p1[0], p1[1]), net)
                    put_power(net, run[len(run) // 2], v)

    # wire signal nets (MST over stub ends)
    order = sorted([n for n in net_ends if n not in GROUNDS and n not in RAILS], key=lambda n: len(net_ends[n]))
    pending = []
    for net in order:
        ends = [e for e, _ in net_ends[net]]
        ends.sort(key=lambda q: -endpc.get(q, 0))     # grow the tree from the biggest part (IC)
        # greedy Steiner tree: connect the nearest remaining end to the tree (end points or T onto existing wires)
        tree_pts, tree_segs, todo = [ends[0]], [], ends[1:]
        while todo:
            cands = []
            for e in todo:
                for t in tree_pts:
                    cands.append((abs(e[0] - t[0]) + abs(e[1] - t[1]), e, t))
                for (x1, y1, x2, y2) in tree_segs:
                    if y1 == y2 and min(x1, x2) < e[0] < max(x1, x2):
                        cands.append((abs(e[1] - y1) - 0.01, e, (e[0], y1)))
                    if x1 == x2 and min(y1, y2) < e[1] < max(y1, y2):
                        cands.append((abs(e[0] - x1) - 0.01, e, (x1, e[1])))
            cands.sort()
            e = cands[0][1]
            ok = False
            for _, ee, t in [c for c in cands if c[1] == e][:16]:
                n0 = len(sh.segs)
                if sh.route(e, t, net):
                    new = [s[:4] for s in sh.segs[n0:]]
                    tree_segs += new
                    for s in new:
                        tree_pts += [(s[0], s[1]), (s[2], s[3])]
                    ok = True
                    break
            if not ok:
                sh.fallbacks.append(net)
                t = min((q for q in tree_pts if q in ends), key=lambda q: abs(e[0] - q[0]) + abs(e[1] - q[1]))
                for q in (e, t):
                    if (q, net) not in [(l[0], l[1]) for l in getattr(sh, "_lab", [])]:
                        sh.__dict__.setdefault("_lab", []).append((q, net))
            tree_pts.append(e)
            todo.remove(e)
        # one global label if the net exists on other sheets, else one small local name label
        if not (len(net_sheets[net]) == 1 and net.startswith("~")):
            pending.append(net)
    # choose the label anchor (stub end) whose label box is clearest
    lab_boxes = []
    for net in pending:
        glob = len(net_sheets[net]) > 1
        h = 1.27 if glob else 1.0
        best = None
        for k, (pt, v) in enumerate(net_ends[net]):
            ang = {(1, 0): 0, (-1, 0): 180, (0, -1): 90, (0, 1): 270}[v]
            if glob:
                bx = label_box(pt, ang, net, h, True)
            else:                       # local label text sits above/left of the wire
                n = len(net) * 0.92 * h + 0.4
                bx = {0: (pt[0], pt[1] - 1.9, pt[0] + n, pt[1] - 0.1), 180: (pt[0] - n, pt[1] - 1.9, pt[0], pt[1] - 0.1),
                      90: (pt[0] - 1.9, pt[1] - n, pt[0] - 0.1, pt[1]), 270: (pt[0] - 1.9, pt[1], pt[0] - 0.1, pt[1] + n)}[ang]
            c = k * 0.05
            for t in sh.segs:
                sb = (min(t[0], t[2]) - 0.25, min(t[1], t[3]) - 0.25, max(t[0], t[2]) + 0.25, max(t[1], t[3]) + 0.25)
                c += ov(bx, sb) * (1 if t[4] == net else 3)
            for o in full_boxes:
                c += ov(bx, o) * 4
            for o in lab_boxes + sh.tobst:
                c += ov(bx, o) * 5
            if best is None or c < best[0]:
                best = (c, pt, ang, bx)
        _, pt, ang, bx = best
        lab_boxes.append(bx)
        if not glob:
            sh.labels.append(LocalLabel(text=net, position=Position(pt[0], pt[1], ang),
                                        effects=Effects(font=Font(height=1.0, width=1.0),
                                                        justify=Justify(horizontally="left" if ang in (0, 90) else "right", vertically="bottom")),
                                        uuid=uid()))
        else:
            sh.glabels.append(GlobalLabel(text=net, shape="passive", position=Position(pt[0], pt[1], ang),
                                          effects=Effects(font=Font(height=1.27, width=1.27),
                                                          justify=Justify(horizontally="left" if ang in (0, 90) else "right")),
                                          uuid=uid(),
                                          properties=[Property(key="Intersheet References", value="${INTERSHEET_REFS}", id=0,
                                                               position=Position(pt[0], pt[1], 0), effects=hid())]))
    for pt, v, net in getattr(sh, "nowire", []):
        ang = {(1, 0): 0, (-1, 0): 180, (0, -1): 90, (0, 1): 270}[v]
        if len(net_sheets[net]) > 1:
            sh.glabels.append(GlobalLabel(text=net, shape="passive", position=Position(pt[0], pt[1], ang),
                                          effects=Effects(font=Font(height=1.27, width=1.27), justify=Justify(horizontally="left" if ang in (0, 90) else "right")),
                                          uuid=uid(), properties=[Property(key="Intersheet References", value="${INTERSHEET_REFS}", id=0,
                                                                           position=Position(pt[0], pt[1], 0), effects=hid())]))
        else:
            sh.labels.append(LocalLabel(text=net, position=Position(pt[0], pt[1], ang),
                                        effects=Effects(font=Font(height=1.0, width=1.0), justify=Justify(horizontally="left" if ang in (0, 90) else "right", vertically="bottom")),
                                        uuid=uid()))
    # fallback local labels
    for q, net in getattr(sh, "_lab", []):
        if len(net_sheets[net]) == 1 and any(l.text == net and (l.position.X, l.position.Y) == q for l in sh.labels):
            continue
        v = next((vv for e, vv in net_ends[net] if e == q), (1, 0))
        ang = {(1, 0): 0, (-1, 0): 180, (0, -1): 90, (0, 1): 270}[v]
        if len(net_sheets[net]) > 1:
            if not any(l.text == net and (l.position.X, l.position.Y) == q for l in sh.glabels):
                sh.glabels.append(GlobalLabel(text=net, shape="passive", position=Position(q[0], q[1], ang),
                                              effects=Effects(font=Font(height=1.27, width=1.27), justify=Justify(horizontally="left" if ang in (0, 90) else "right")),
                                              uuid=uid(), properties=[Property(key="Intersheet References", value="${INTERSHEET_REFS}", id=0,
                                                                               position=Position(q[0], q[1], 0), effects=hid())]))
            continue
        sh.labels.append(LocalLabel(text=net, position=Position(q[0], q[1], ang),
                                    effects=Effects(font=Font(height=1.27, width=1.27),
                                                    justify=Justify(horizontally="left" if ang in (0, 90) else "right", vertically="bottom")),
                                    uuid=uid()))

    # split wires at T points (KiCad only connects wire end points)
    endpts = {}
    for s in sh.segs:
        for q in ((s[0], s[1]), (s[2], s[3])):
            endpts.setdefault(q, set()).add(s[4])
    newsegs = []
    for s in sh.segs:
        cut = sorted({q for q, nets in endpts.items() if s[4] in nets and sh.on_seg(q[0], q[1], s)
                      and q not in ((s[0], s[1]), (s[2], s[3]))},
                     key=lambda q: abs(q[0] - s[0]) + abs(q[1] - s[1]))
        pts = [(s[0], s[1])] + cut + [(s[2], s[3])]
        for p0, p1 in zip(pts, pts[1:]):
            newsegs.append((p0[0], p0[1], p1[0], p1[1], s[4]))
    # drop exact duplicates (same net, same span)
    seen, segs2 = set(), []
    for s in newsegs:
        k = (min((s[0], s[1]), (s[2], s[3])), max((s[0], s[1]), (s[2], s[3])), s[4])
        if k not in seen:
            seen.add(k); segs2.append(s)
    sh.segs = segs2
    sh.wires = [Connection(type="wire", points=[Position(s[0], s[1]), Position(s[2], s[3])],
                           stroke=Stroke(width=0, type="default"), uuid=uid()) for s in sh.segs]

    # junctions: any point touched by >=3 wire ends, or a wire end on another same-net wire interior
    cnt = {}
    for s in sh.segs:
        for q in ((s[0], s[1]), (s[2], s[3])):
            cnt[q] = cnt.get(q, 0) + 1
    jpts = {q for q, c in cnt.items() if c >= 3}
    for s in sh.segs:
        for q in list(cnt):
            if sh.points.get(q) == s[4] and sh.on_seg(q[0], q[1], s) and q not in ((s[0], s[1]), (s[2], s[3])):
                jpts.add(q)
    sh.juncs = [Junction(position=Position(*q), diameter=0, uuid=uid()) for q in sorted(jpts)]

    # obstacles for field placement
    for l in sh.labels:
        sh.tobst.append(label_box((l.position.X, l.position.Y), int(l.position.angle or 0), l.text, 1.27, False))
    for l in sh.glabels:
        sh.tobst.append(label_box((l.position.X, l.position.Y), int(l.position.angle or 0), l.text, 1.27, True))
    seg_boxes = [(min(t[0], t[2]) - 0.25, min(t[1], t[3]) - 0.25, max(t[0], t[2]) + 0.25, max(t[1], t[3]) + 0.25) for t in sh.segs]
    for (x, y, txt) in NOTES.get(sheet_name, []):
        n = max(len(l) for l in txt.split("\n"))
        sh.tobst.append((x, y - 0.5, x + n * 0.92 * 1.27, y + 1.9 * len(txt.split("\n"))))
        sh.texts.append(Text(text=txt.replace("\n", "\\n"), position=Position(x, y, 0),
                             effects=Effects(font=Font(height=1.27, width=1.27), justify=Justify(horizontally="left", vertically="top")),
                             uuid=uid()))
    placed_txt = []
    seg_boxes += pin_lines

    def cost(box, own):
        c = 0.0
        for o in full_boxes:
            c += ov(box, o) * (8 if o is own else 4)
        for o in seg_boxes:
            c += ov(box, o) * 3
        for o in sh.tobst + placed_txt:
            c += ov(box, o) * 5
        if box[0] < 8 or box[1] < 8 or box[2] > 410 or box[3] > 262:
            c += 100
        return c

    # power symbol values
    for ss, net, pt, v, body in sh.pwr:
        vx, vy = v
        hv = 1.0
        b0 = tbox(0, 0, net, hv); w, hh = b0[2] - b0[0], b0[3] - b0[1]
        if vx:
            cands = [(pt[0] + vx * (3.0 + w / 2), pt[1]), (pt[0] + vx * 1.6, pt[1] - 1.5 - hh / 2), (pt[0] + vx * 1.6, pt[1] + 1.5 + hh / 2)]
        else:
            cands = [(pt[0], pt[1] + vy * (3.1 + hh / 2)), (pt[0] + 1.6 + w / 2, pt[1] + vy * 2.0), (pt[0] - 1.6 - w / 2, pt[1] + vy * 2.0)]
        best = None
        for i, c in enumerate(cands):
            bx = tbox(c[0], c[1], net, hv)
            cc = cost(bx, None) - ov(bx, body) * 5 + i * 0.3
            if best is None or cc < best[0]:
                best = (cc, c, bx)
        placed_txt.append(best[2])
        for pr in ss.properties:
            if pr.key == "Value":
                pr.position = Position(round(best[1][0], 3), round(best[1][1], 3), pr.position.angle)

    # component symbols
    for p, sym, x, y, rot, mirror in placed:
        ss = SchematicSymbol()
        ss.libraryNickname, ss.entryName = p.sym.split(":")
        ss.position = Position(x, y, rot)
        ss.mirror = "y" if mirror else None
        ss.unit, ss.inBom, ss.onBoard, ss.uuid = 1, True, True, uid()
        bb = body_box(sym, x, y, rot, mirror) or (x - 2, y - 2, x + 2, y + 2)
        own = next((o for o in full_boxes if o == bb), None)
        fa = rot if rot in (90, 270) else 0
        H = 1.27
        HV = 1.0 if p.sym.startswith("Device:") else 1.27
        rb0 = tbox(0, 0, p.ref, H); vb0 = tbox(0, 0, p.value, HV)
        rw, rh = rb0[2] - rb0[0], rb0[3] - rb0[1]
        vw, vh = vb0[2] - vb0[0], vb0[3] - vb0[1]
        cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
        g = 0.6
        cands = []
        for sx in (0, 2.54, -2.54, 5.08, -5.08):
            cands.append(((cx + sx, bb[1] - g - rh / 2), (cx + sx, bb[3] + g + vh / 2)))                 # ref above, value below
            cands.append(((cx + sx, bb[1] - g - vh - rh / 2), (cx + sx, bb[1] - g - vh / 2)))            # both above
            cands.append(((cx + sx, bb[3] + g + rh / 2), (cx + sx, bb[3] + g + rh + vh / 2)))            # both below
        for sy in (0, -2.54, 2.54, -5.08, 5.08):
            cands.append(((bb[2] + g + rw / 2, cy - rh / 2 + sy), (bb[2] + g + vw / 2, cy + vh / 2 + sy)))   # right stacked
            cands.append(((bb[0] - g - rw / 2, cy - rh / 2 + sy), (bb[0] - g - vw / 2, cy + vh / 2 + sy)))   # left stacked
        cands.append(((bb[2] + g + rw / 2, cy), (bb[0] - g - vw / 2, cy)))
        for (rx, vx_) in ((bb[0] + rw / 2, bb[0] + vw / 2), (bb[2] - rw / 2, bb[2] - vw / 2)):
            cands.append(((rx, bb[1] - g - rh / 2), (vx_, bb[3] + g + vh / 2)))
            cands.append(((rx, bb[1] - g - vh - rh / 2), (vx_, bb[1] - g - vh / 2)))
            cands.append(((rx, bb[3] + g + rh / 2), (vx_, bb[3] + g + rh + vh / 2)))
        cands.append(((bb[0] - g - rw / 2, cy), (bb[2] + g + vw / 2, cy)))
        two = len(G0.all_pins(sym)) <= 2 and p.sym.startswith("Device:") and rot in (0, 180)
        if two:                                   # vertical 2-pin parts: prefer text at the side
            cands = cands[15:17] + cands[:15] + cands[17:]
        fo = FIELDS.get(p.ref)
        if fo:
            ex, ey, just = fo["ref"]
            rc = (ex + rw / 2 if just == "left" else ex - rw / 2 if just == "right" else ex, ey)
            vc = None
        else:
            best = None
            for i, (rc, vc) in enumerate(cands):
                rbx, vbx = tbox(*rc, p.ref, H), tbox(*vc, p.value, HV)
                c = cost(rbx, own) + cost(vbx, own) + ov(rbx, vbx) * 10 + i * 0.01
                if best is None or c < best[0]:
                    best = (c, rc, vc)
            _, rc, vc = best
            if best[0] > 0.5:
                sh.__dict__.setdefault("txt_conf", []).append((p.ref, round(best[0], 1)))
        placed_txt.append(tbox(*rc, p.ref, H))
        if vc:
            placed_txt.append(tbox(*vc, p.value, HV))
        rp = (round(rc[0], 3), round(rc[1], 3))
        vp = (round(vc[0], 3), round(vc[1], 3)) if vc else (x, y)
        ss.properties = [
            Property(key="Reference", value=p.ref, id=0, position=Position(*rp, fa), effects=fnt(H)),
            Property(key="Value", value=p.value, id=1, position=Position(*vp, fa), effects=fnt(HV) if vc else hid()),
            Property(key="Footprint", value=p.fp, id=2, position=Position(x, y, 0), effects=hid()),
            Property(key="Datasheet", value="", id=3, position=Position(x, y, 0), effects=hid()),
            Property(key="LCSC", value=p.lcsc, id=4, position=Position(x, y, 0), effects=hid()),
            Property(key="MPN", value=p.mpn or p.value, id=5, position=Position(x, y, 0), effects=hid()),
        ]
        ss.pins = {sp.number: uid() for sp in G0.all_pins(sym)}
        sh.syms.append(ss)
        refs_out.append((ss.uuid, p.ref, p.value, p.fp))
    sh.libsyms = libsyms
    return sh


def to_file(sh, path, title, page_text):
    sch = Schematic.create_new()
    sch.version, sch.generator, sch.uuid = 20211123, "eeschema", uid()
    sch.paper = PageSettings(paperSize="A3")
    sch.titleBlock = TitleBlock(title=title, date="2026-10-19", revision="E",
                                comments={1: "DCDC LLC + 4SBB, 12-48 V in, 1.5-48 V / 5 A out, STM32G474",
                                          2: page_text})
    for libid, s in sh.libsyms.items():
        e = copy.deepcopy(s)
        e.libraryNickname, e.entryName = libid.split(":")
        for u in e.units:
            u.libraryNickname = None
            u.entryName = libid.split(":")[1]
        sch.libSymbols.append(e)
    sch.schematicSymbols = sh.syms
    sch.graphicalItems = sh.wires
    sch.labels = sh.labels
    sch.globalLabels = sh.glabels
    sch.junctions = sh.juncs
    sch.noConnects = sh.ncs
    sch.texts = sh.texts
    sch.to_file(path)
    return sch.uuid


def build(outdir):
    import os
    os.makedirs(outdir, exist_ok=True)
    net_sheets = {}
    for sname, (blocks, _t) in SHEETS.items():
        for p in D.P:
            if p.block in blocks:
                for n in p.pins.values():
                    net_sheets.setdefault(n, set()).add(sname)
    root = Schematic.create_new()
    root.version, root.generator, root.uuid = 20211123, "eeschema", uid()
    root.paper = PageSettings(paperSize="A3")
    root.titleBlock = TitleBlock(title="DCDC LLC + 4SBB G474 - top level", date="2026-10-19", revision="E",
                                 comments={1: "Isolated 12-48 V -> 1.5-48 V / 5 A / 50 W; STM32G474RBT3; isolated CAN",
                                           2: "Sheets connect through global labels and power symbols"})
    sheet_insts = [HierarchicalSheetInstance(instancePath="/", page="1")]
    sym_insts, report = [], {}
    for i, (sname, (blocks, title)) in enumerate(SHEETS.items()):
        refs = []
        sh = build_sheet(sname, blocks, net_sheets, refs)
        fname = f"{sname}.kicad_sch"
        to_file(sh, f"{outdir}/{fname}", title, f"Sheet {i + 2}: {title}")
        su = uid()
        col, row = i % 4, i // 4
        x0, y0 = 25 + col * 95, 40 + row * 70
        hs = HierarchicalSheet(position=Position(x0, y0), width=80, height=50, uuid=su,
                               stroke=Stroke(width=0.1524, type="solid"),
                               sheetName=Property(key="Sheet name", value=title.split(" - ")[0][:40], id=0,
                                                  position=Position(x0, y0 - 0.7, 0), effects=Effects(font=Font(height=1.27, width=1.27), justify=Justify(horizontally="left", vertically="bottom"))),
                               fileName=Property(key="Sheet file", value=fname, id=1,
                                                 position=Position(x0, y0 + 50.6, 0), effects=Effects(font=Font(height=1.27, width=1.27), justify=Justify(horizontally="left", vertically="top"))))
        root.sheets.append(hs)
        sheet_insts.append(HierarchicalSheetInstance(instancePath=f"/{su}", page=str(i + 2)))
        for (u, ref, val, fp) in refs:
            sym_insts.append(SymbolInstance(path=f"/{su}/{u}", reference=ref, unit=1, value=val, footprint=fp))
        report[sname] = dict(wires=len(sh.wires), glabels=len(sh.glabels), fallback_labels=len(sh.labels),
                             fallback_nets=sorted(set(sh.fallbacks)), power_syms=sum(1 for s in sh.syms if s.libraryNickname == "pwr"), text_conflicts=getattr(sh, "txt_conf", []))
    root.sheetInstances = sheet_insts
    root.symbolInstances = sym_insts
    root.to_file(f"{outdir}/{PROJECT}.kicad_sch")
    json.dump({si.reference: si.path for si in sym_insts if not si.reference.startswith("#")},
              open(f"{outdir}/uuid_paths.json", "w"), indent=0)
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "/home/claude/dcdc/sch2")

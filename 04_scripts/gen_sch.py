"""Generate a KiCad 7 schematic (EasyEDA Pro importable) from design.py.

Every pin gets a short wire stub and a local net label; unused pins get no-connect flags.
Symbols come from the stock KiCad 7 libraries (flattened, embedded) plus two custom symbols.
"""
import copy, math, re, sys, uuid as uuidlib
from kiutils.schematic import Schematic
from kiutils.symbol import SymbolLib, Symbol, SymbolPin
from kiutils.items.common import Position, Property, Effects, Font, Justify, Stroke, ColorRGBA
from kiutils.items.syitems import SyRect, Fill as SyFill
from kiutils.items.schitems import (SymbolInstance, SchematicSymbol, LocalLabel, Connection, NoConnect, Text,
                                    SymbolProjectInstance, SymbolProjectPath, HierarchicalSheetInstance)
from kiutils.items.common import TitleBlock, PageSettings

sys.path.insert(0, "/home/claude/dcdc")
import design as D

LIBDIR = "/usr/share/kicad/symbols"
PROJECT = "DCDC_4SBB_G474"
G = 2.54
uid = lambda: str(uuidlib.uuid4())
_lib_cache = {}


def snap(v, g=1.27):
    return round(round(v / g) * g, 4)


def font(size=1.27):
    return Effects(font=Font(width=size, height=size))


# ---------------------------------------------------------------- symbol libraries
def load_lib_symbol(libid):
    lib, name = libid.split(":")
    if lib not in _lib_cache:
        _lib_cache[lib] = SymbolLib.from_file(f"{LIBDIR}/{lib}.kicad_sym")
    d = {s.entryName: s for s in _lib_cache[lib].symbols}
    chain = [d[name]]
    while chain[-1].extends:
        chain.append(d[chain[-1].extends])
    base = copy.deepcopy(chain[-1])
    child = chain[0]
    if len(chain) > 1:
        cp = {p.key: p for p in child.properties}
        for p in base.properties:
            if p.key in cp:
                p.value = cp[p.key].value
        have = {p.key for p in base.properties}
        for k, p in cp.items():
            if k not in have:
                base.properties.append(copy.deepcopy(p))
    base.entryName = name
    base.extends = None
    for u in base.units:
        u.entryName = name
    base.libraryNickname = lib
    return base


def pin(num, name, x, y, ang, etype="passive", length=2.54, hide=False):
    p = SymbolPin(electricalType=etype, graphicalStyle="line", position=Position(x, y, ang), length=length,
                  name=name, number=num, hide=hide)
    return p


def custom_symbol(name, left, right, width=15.24, ref="U", fp="", desc=""):
    """left/right: list of (num, name, etype) or None for a gap, top to bottom."""
    n = max(len(left), len(right))
    h = (n + 1) * G
    top = snap(h / 2, G)
    s = Symbol(libraryNickname="custom", entryName=name, inBom=True, onBoard=True)
    s.pinNames = True
    s.pinNamesOffset = 1.016
    s.properties = [
        Property(key="Reference", value=ref, id=0, position=Position(0, top + 2.54, 0), effects=font()),
        Property(key="Value", value=name, id=1, position=Position(0, -top - 2.54, 0), effects=font()),
        Property(key="Footprint", value=fp, id=2, position=Position(0, 0, 0), effects=Effects(font=Font(height=1.27, width=1.27), hide=True)),
        Property(key="Datasheet", value="", id=3, position=Position(0, 0, 0), effects=Effects(font=Font(height=1.27, width=1.27), hide=True)),
        Property(key="Description", value=desc, id=4, position=Position(0, 0, 0), effects=Effects(font=Font(height=1.27, width=1.27), hide=True)),
    ]
    body = Symbol(libraryNickname=None, entryName=name, unitId=0, styleId=1)
    body.graphicItems = [SyRect(start=Position(-width / 2, top), end=Position(width / 2, -top),
                                stroke=Stroke(width=0.254, type="default"), fill=SyFill(type="background"))]
    pins_u = Symbol(libraryNickname=None, entryName=name, unitId=1, styleId=1)
    seen = {}
    for side, items in (("L", left), ("R", right)):
        for i, it in enumerate(items):
            if it is None:
                continue
            num, pname, et = it
            y = snap(top - (i + 1) * G, G)
            x = -width / 2 - G if side == "L" else width / 2 + G
            ang = 0 if side == "L" else 180
            key = (side, pname)
            hide = False
            if pname in seen and seen[pname][0] == side and pname not in ("NC",):
                # stack same-name power pins on the first one, hidden
                y = seen[pname][1]
                hide = True
            else:
                seen[pname] = (side, y)
            pins_u.pins.append(pin(num, pname, x, y, ang, et, hide=hide))
    s.units = [body, pins_u]
    return s


CUSTOM = {
    "UCC27211": custom_symbol(
        "UCC27211",
        left=[("1", "VDD", "power_in"), ("5", "HI", "input"), ("6", "LI", "input"), None, ("7", "VSS", "power_in"),
              ("9", "EP", "passive")],
        right=[("2", "HB", "passive"), ("3", "HO", "output"), ("4", "HS", "passive"), None, ("8", "LO", "output")],
        width=12.7, fp=D.FP["SOIC8EP"], desc="120 V 4 A half-bridge driver, independent inputs"),
    "CA-IS3062VW": custom_symbol(
        "CA-IS3062VW",
        left=[("1", "VCC", "power_in"), ("7", "VCCL", "power_in"), None, ("3", "TXD", "input"), ("5", "RXD", "output"),
              None, ("2", "GND1", "power_in"), ("8", "GND1", "passive"), None, ("4", "NC", "no_connect"),
              ("6", "NC", "no_connect")],
        right=[("16", "VISO", "power_out"), ("11", "VISO", "passive"), None, ("13", "CANH", "bidirectional"),
               ("12", "CANL", "bidirectional"), None, ("9", "GND2", "power_out"), ("10", "GND2", "passive"),
               ("15", "GND2", "passive"), None, ("14", "NC", "no_connect")],
        width=17.78, fp=D.FP["SOIC16W"], desc="Isolated CAN transceiver with integrated isolated power, 5 kVrms"),
    "UCC27524": custom_symbol(
        "UCC27524",
        left=[("6", "VDD", "power_in"), ("2", "INA", "input"), ("4", "INB", "input"), ("1", "ENA", "input"),
              ("8", "ENB", "input"), ("3", "GND", "power_in")],
        right=[("7", "OUTA", "output"), None, ("5", "OUTB", "output")],
        width=12.7, fp=D.FP["SOIC8"], desc="Dual 5 A low-side gate driver"),
    "CA-IS3642LVW": custom_symbol(
        "CA-IS3642LVW",
        left=[("1", "VDD", "power_in"), ("7", "VDDL", "power_in"), None, ("3", "VI1", "input"), ("4", "VI2", "input"),
              ("5", "VO3", "output"), ("6", "VO4", "output"), None, ("2", "GNDA", "power_in"), ("8", "GNDA", "passive")],
        right=[("16", "VISO", "power_out"), ("10", "SEL", "input"), None, ("14", "VO1", "output"), ("13", "VO2", "output"),
               ("12", "VI3", "input"), ("11", "VI4", "input"), None, ("9", "GNDB", "power_out"), ("15", "GNDB", "passive")],
        width=17.78, fp=D.FP["SOIC16W"], desc="5 kVrms quad isolator (2 fwd / 2 rev) with 650 mW isolated DC-DC"),
    "CA-IS3742": custom_symbol(
        "CA-IS3742",
        left=[("1", "VDDA", "power_in"), ("7", "ENA", "input"), None, ("3", "VI1", "input"), ("4", "VI2", "input"),
              ("5", "VO3", "output"), ("6", "VO4", "output"), None, ("2", "GNDA", "power_in"), ("8", "GNDA", "passive")],
        right=[("16", "VDDB", "power_in"), ("10", "ENB", "input"), None, ("14", "VO1", "output"), ("13", "VO2", "output"),
               ("12", "VI3", "input"), ("11", "VI4", "input"), None, ("9", "GNDB", "power_in"), ("15", "GNDB", "passive")],
        width=17.78, fp=D.FP["SOIC16W"], desc="5 kVrms quad digital isolator, 2 fwd / 2 rev, default-low (L) outputs"),
    "PA3855": custom_symbol(
        "PA3855",
        left=[("1", "P1*", "passive"), None, ("3", "P3", "passive"), None, ("4", "AUX4*", "passive"), None,
              ("5", "AUX5", "passive")],
        right=[("9", "S9*", "passive"), None, ("6", "S6", "passive"), None, ("10", "S10*", "passive"), None,
               ("7", "S7", "passive")],
        width=15.24, ref="T", fp=D.FP["TX_EP13"],
        desc="Pulse PA3855 EP13 flyback transformer; * = dot (winding start); pri 1-3, aux 4-5, sec 9-6 and 10-7"),
}


def get_symbol(libid):
    if libid.startswith("custom:"):
        s = copy.deepcopy(CUSTOM[libid.split(":")[1]])
        return s
    return load_lib_symbol(libid)


# ---------------------------------------------------------------- geometry
def all_pins(sym, unit=1):
    out = []
    for u in sym.units:
        if u.unitId in (0, unit):
            out.extend(u.pins)
    return out


def xform(px, py, rot):
    r = math.radians(rot)
    x = px * math.cos(r) - py * math.sin(r)
    y = px * math.sin(r) + py * math.cos(r)
    return x, -y          # lib (y up) -> sheet (y down)


def pin_geom(p, sx, sy, rot):
    dx, dy = xform(p.position.X, p.position.Y, rot)
    a = (p.position.angle + 180 + rot) % 360        # outward direction in lib coords
    vx, vy = round(math.cos(math.radians(a))), -round(math.sin(math.radians(a)))
    return (snap(sx + dx), snap(sy + dy)), (vx, vy)


def bbox(sym, rot, pins_map):
    xs, ys = [], []
    lab = 0
    for p in all_pins(sym):
        (x, y), (vx, vy) = pin_geom(p, 0, 0, rot)
        n = pins_map.get(p.number, "")
        L = G + (len(n) * 1.05 + 2 if n and n != "NC" else 1)
        xs += [x, x + vx * L]
        ys += [y, y + vy * L]
    # symbol body extents
    for u in sym.units:
        for gi in getattr(u, "graphicItems", []):
            for attr in ("start", "end", "center"):
                q = getattr(gi, attr, None)
                if q is not None:
                    x, y = xform(q.X, q.Y, rot); xs.append(x); ys.append(y)
    return min(xs), min(ys), max(xs), max(ys)


# ---------------------------------------------------------------- build
def build(out_path, fmt="v6"):
    import json
    v6 = fmt == "v6"
    sym_instances, uuid_map = [], {}
    sch = Schematic.create_new()
    sch.version = 20211123 if v6 else 20230121
    sch.generator = "eeschema"
    sch.uuid = uid()
    sch.paper = PageSettings(paperSize="A1")
    sch.titleBlock = TitleBlock(title="4-Switch Buck-Boost 12-48V -> 1.5-48V 5A 50W, STM32G474 HRTIM, isolated CAN",
                                date="2026-10-17", revision="A",
                                comments={1: "fsw 150 kHz, L 22 uH, NCEP0140AG/NCEP0160AG, UCC27211 x2",
                                          2: "Generated for EasyEDA Pro import (KiCad 7 format). Swap footprints via LCSC field."})
    root_path = "/" + sch.uuid

    libsyms = {}
    placed = []      # (part, sym, x, y, rot)

    # block layout on A1 (841 x 594): (x0, y0, width)
    regions = {
        "H_LLC": (15, 25, 270), "I_PRI": (15, 250, 270),
        "A_POWER": (300, 25, 265), "B_DRIVE": (300, 120, 265), "E_SENSE": (300, 200, 265), "C_AUX": (300, 300, 265),
        "D_MCU": (595, 25, 225), "F_CAN": (595, 250, 225), "G_IO": (595, 370, 225),
    }
    texts = []
    for blk, (x0, y0, w) in regions.items():
        texts.append(Text(text=D.BLOCK_TITLES[blk], position=Position(x0, y0 - 8, 0),
                          effects=Effects(font=Font(height=2.5, width=2.5, bold=True), justify=Justify(horizontally="left")),
                          uuid=uid()))
        parts = [p for p in D.P if p.block == blk]
        # big parts first
        parts.sort(key=lambda p: -len(p.pins))
        cx, cy, row_h = x0, y0, 0
        for p in parts:
            sym = get_symbol(p.sym)
            rot = 90 if p.sym in ("Device:R", "Device:C", "Device:C_Polarized", "Device:L", "Device:Fuse",
                                  "Device:FerriteBead_Small", "Device:Thermistor_NTC") else 0
            bx0, by0, bx1, by1 = bbox(sym, rot, p.pins)
            wdt, hgt = bx1 - bx0 + 5, by1 - by0 + 6
            if rot == 90:
                hgt = max(hgt, 12.7)
            if cx + wdt > x0 + w and cx > x0:
                cx, cy, row_h = x0, cy + row_h, 0
            sx, sy = snap(cx - bx0, G), snap(cy - by0, G)
            placed.append((p, sym, sx, sy, rot))
            cx += wdt
            row_h = max(row_h, hgt)
            libsyms.setdefault(p.sym, sym)

    # embed library symbols (custom ones under 'custom:' nickname)
    for libid, s in libsyms.items():
        e = copy.deepcopy(s)
        e.libraryNickname, e.entryName = libid.split(":")
        for u in e.units:
            u.libraryNickname = None
            u.entryName = libid.split(":")[1]
        sch.libSymbols.append(e)

    labels, wires, ncs = [], [], []
    report = []
    for p, sym, sx, sy, rot in placed:
        ss = SchematicSymbol()
        ss.libraryNickname, ss.entryName = p.sym.split(":")
        ss.position = Position(sx, sy, rot)
        ss.unit = 1
        ss.inBom = True
        ss.onBoard = True
        ss.dnp = None if v6 else p.dnp
        ss.uuid = uid()
        hid = Effects(font=Font(height=1.27, width=1.27), hide=True)
        bx0, by0, bx1, by1 = bbox(sym, rot, {})
        if rot == 90:
            by0, by1 = -2.3, 2.0
        ss.properties = [
            Property(key="Reference", value=p.ref, id=0, position=Position(sx, snap(sy + by0 - 1.5), rot), effects=font()),
            Property(key="Value", value=p.value, id=1, position=Position(sx, snap(sy + by1 + (1.8 if rot == 90 or len(p.pins) < 20 else 12)), rot), effects=font()),
            Property(key="Footprint", value=p.fp, id=2, position=Position(sx, sy, 0), effects=hid),
            Property(key="Datasheet", value="", id=3, position=Position(sx, sy, 0), effects=hid),
            Property(key="LCSC", value=p.lcsc, id=4, position=Position(sx, sy, 0), effects=hid),
            Property(key="MPN", value=p.mpn or p.value, id=5, position=Position(sx, sy, 0), effects=hid),
            Property(key="Note", value=p.note, id=6, position=Position(sx, sy, 0), effects=hid),
        ]
        ss.pins = {}
        for sp in all_pins(sym):
            ss.pins[sp.number] = uid()
        uuid_map[p.ref] = ss.uuid
        if v6:
            ss.instances = []
            sym_instances.append(SymbolInstance(path="/" + ss.uuid, reference=p.ref, unit=1, value=p.value, footprint=p.fp))
        else:
            ss.instances = [SymbolProjectInstance(name=PROJECT, paths=[SymbolProjectPath(
                sheetInstancePath=root_path, reference=p.ref, unit=1)])]
        sch.schematicSymbols.append(ss)

        # pins grouped by connection point
        groups = {}
        for sp in all_pins(sym):
            pt, v = pin_geom(sp, sx, sy, rot)
            groups.setdefault(pt, []).append((sp, v))
        sym_nums = {sp.number for sp in all_pins(sym)}
        missing = set(p.pins) - sym_nums
        assert not missing, f"{p.ref}: pins {missing} not in symbol {p.sym}"
        for pt, lst in groups.items():
            nets = {p.pins.get(sp.number) for sp, _ in lst}
            nets.discard(None)
            assert len(nets) <= 1, f"{p.ref} stacked pins at {pt} map to different nets {nets}"
            v = lst[0][1]
            if not nets or nets == {"NC"}:
                ncs.append(NoConnect(position=Position(*pt), uuid=uid()))
                continue
            net = nets.pop()
            end = (snap(pt[0] + v[0] * G), snap(pt[1] + v[1] * G))
            wires.append(Connection(type="wire", points=[Position(*pt), Position(*end)],
                                    stroke=Stroke(width=0, type="default"), uuid=uid()))
            ang = {(1, 0): 0, (-1, 0): 180, (0, -1): 90, (0, 1): 270}[v]
            just = Justify(horizontally="left" if ang in (0, 90) else "right", vertically="bottom")
            labels.append(LocalLabel(text=net, position=Position(end[0], end[1], ang),
                                     effects=Effects(font=Font(height=1.27, width=1.27), justify=just), uuid=uid()))

    # PWR_FLAGs in a strip at the bottom of the sheet
    pf = load_lib_symbol("power:PWR_FLAG")
    sch.libSymbols.append(pf)
    fx, fy = 300, 540
    texts.append(Text(text="ERC power flags (no circuit function)", position=Position(fx - 10, fy - 15, 0),
                      effects=Effects(font=Font(height=1.5, width=1.5), justify=Justify(horizontally="left")), uuid=uid()))
    for i, net in enumerate(D.PWR_FLAG_NETS):
        x = fx + i * 25.4
        ss = SchematicSymbol(libraryNickname="power", entryName="PWR_FLAG", position=Position(x, fy, 0), unit=1,
                             inBom=False, onBoard=True, uuid=uid())
        ref = f"#FLG{i+1:02d}"
        ss.properties = [
            Property(key="Reference", value=ref, id=0, position=Position(x, fy + 1.9, 0), effects=Effects(font=Font(height=1.27, width=1.27), hide=True)),
            Property(key="Value", value="PWR_FLAG", id=1, position=Position(x, fy - 3.8, 0), effects=font()),
            Property(key="Footprint", value="", id=2, position=Position(x, fy, 0), effects=Effects(font=Font(height=1.27, width=1.27), hide=True)),
            Property(key="Datasheet", value="~", id=3, position=Position(x, fy, 0), effects=Effects(font=Font(height=1.27, width=1.27), hide=True)),
        ]
        ss.pins = {"1": uid()}
        if v6:
            ss.instances = []
            sym_instances.append(SymbolInstance(path="/" + ss.uuid, reference=ref, unit=1, value="PWR_FLAG", footprint=""))
        else:
            ss.instances = [SymbolProjectInstance(name=PROJECT, paths=[SymbolProjectPath(sheetInstancePath=root_path, reference=ref, unit=1)])]
        sch.schematicSymbols.append(ss)
        end = (x, fy + G)
        wires.append(Connection(type="wire", points=[Position(x, fy), Position(*end)], stroke=Stroke(width=0, type="default"), uuid=uid()))
        labels.append(LocalLabel(text=net, position=Position(end[0], end[1], 270),
                                 effects=Effects(font=Font(height=1.27, width=1.27), justify=Justify(horizontally="right", vertically="bottom")), uuid=uid()))

    sch.labels = labels
    sch.graphicalItems = wires
    sch.noConnects = ncs
    sch.texts = texts
    sch.sheetInstances = [HierarchicalSheetInstance(instancePath="/", page="1")]
    if v6:
        sch.symbolInstances = sym_instances
    sch.to_file(out_path)
    json.dump(uuid_map, open(out_path.replace('.kicad_sch', '_uuids.json'), 'w'), indent=0)
    print("parts placed:", len(placed), "labels:", len(labels), "no-connects:", len(ncs))


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "/home/claude/dcdc/out/DCDC_4SBB_G474.kicad_sch", sys.argv[2] if len(sys.argv) > 2 else "v6")

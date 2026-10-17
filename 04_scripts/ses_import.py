"""Import a Freerouting .ses into a KiCad board without the GUI. Usage: ses_import.py board.kicad_pcb board.ses out.kicad_pcb"""
import re, sys
import pcbnew


def sexp(text):
    toks = re.findall(r'\(|\)|"[^"]*"|[^\s()]+', text)
    stack, cur = [], []
    for tk in toks:
        if tk == "(":
            stack.append(cur); cur = []
        elif tk == ")":
            done = cur; cur = stack.pop(); cur.append(done)
        else:
            cur.append(tk.strip('"'))
    return cur[0]


def find(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]


def run(pcb, ses, out):
    b = pcbnew.LoadBoard(pcb)
    tree = sexp(open(ses).read())
    routes = find(tree, "routes")[0]
    res = find(routes, "resolution")[0]
    scale = {"um": 1000.0}[res[1]] / float(res[2])     # file unit -> nm
    to_nm = lambda v: int(round(float(v) * scale))
    stacks = {}
    for ps in find(find(routes, "library_out")[0], "padstack"):
        dia = to_nm(find(ps, "shape")[0][1][2])
        m = re.search(r"_(\d+):(\d+)_um", ps[1])
        drill = int(m.group(2)) * 1000 if m else dia // 2
        stacks[ps[1]] = (dia, drill)
    layers = {b.GetLayerName(l): l for l in range(pcbnew.PCB_LAYER_ID_COUNT) if pcbnew.IsCopperLayer(l)}
    ntr = nvia = 0
    for net in find(find(routes, "network_out")[0], "net"):
        ni = b.FindNet(net[1])
        for w in find(net, "wire"):
            path = find(w, "path")[0]
            layer, width = layers[path[1]], to_nm(path[2])
            pts = [(to_nm(path[i]), -to_nm(path[i + 1])) for i in range(3, len(path), 2)]
            for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
                tr = pcbnew.PCB_TRACK(b)
                tr.SetStart(pcbnew.VECTOR2I(x1, y1)); tr.SetEnd(pcbnew.VECTOR2I(x2, y2))
                tr.SetWidth(width); tr.SetLayer(layer); tr.SetNet(ni)
                b.Add(tr); ntr += 1
        for v in find(net, "via"):
            dia, drill = stacks[v[1]]
            via = pcbnew.PCB_VIA(b)
            via.SetPosition(pcbnew.VECTOR2I(to_nm(v[2]), -to_nm(v[3])))
            via.SetWidth(dia); via.SetDrill(drill); via.SetNet(ni)
            via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            b.Add(via); nvia += 1
    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())
    b.BuildConnectivity()
    unc = b.GetConnectivity().GetUnconnectedCount(False) if hasattr(b.GetConnectivity(), "GetUnconnectedCount") else -1
    pcbnew.SaveBoard(out, b)
    print(f"tracks {ntr}, vias {nvia}, unconnected {unc}")


if __name__ == "__main__":
    run(*sys.argv[1:4])

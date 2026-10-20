"""Rev E finishing after routing: ground floods (F.Cu, In2, B.Cu) per isolation domain at the lowest priority,
fill, then ground stitching (opt/stitch.py logic). usage: finish5.py routed.kicad_pcb out.kicad_pcb"""
import subprocess, sys
import pcbnew
sys.path.insert(0, "/home/claude/dcdc/pcb5")
import place5 as P

mm = pcbnew.FromMM
F, I2, B = pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu
e = 0.6
DOMAINS = [
    ("GNDP", [(e, e), (P.XB - P.BAND, e), (P.XB - P.BAND, P.H - e), (e, P.H - e)]),
    ("GND", [(P.XB + P.BAND, e), (P.W - e, e), (P.W - e, P.YC - P.BAND), (P.XC - P.BAND, P.YC - P.BAND),
             (P.XC - P.BAND, P.H - e), (P.XB + P.BAND, P.H - e)]),
    ("GND_ISO", [(P.XC + P.BAND, P.YC + P.BAND), (P.W - e, P.YC + P.BAND), (P.W - e, P.H - e), (P.XC + P.BAND, P.H - e)]),
]


def main(src, dst):
    b = pcbnew.LoadBoard(src)
    for net, poly in DOMAINS:
        for layer in (F, I2, B):
            z = pcbnew.ZONE(b)
            z.SetLayer(layer)
            z.SetNet(b.FindNet(net))
            ol = z.Outline()
            ol.NewOutline()
            for x, y in poly:
                ol.Append(mm(x), mm(y))
            z.SetLocalClearance(mm(0.3))
            z.SetMinThickness(mm(0.25))
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)   # SMD pads solid, PTH with reliefs
            z.SetThermalReliefGap(mm(0.3))
            z.SetThermalReliefSpokeWidth(mm(0.4))
            z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
            z.SetAssignedPriority(1)
            z.SetZoneName(f"FLOOD_{net}")
            b.Add(z)
    ds = b.GetDesignSettings()
    ds.m_CopperEdgeClearance = mm(0.3)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    tmp = dst + ".tmp.kicad_pcb"
    pcbnew.SaveBoard(tmp, b)
    r = subprocess.run(["python3", "/home/claude/dcdc/opt/stitch.py", tmp, dst], capture_output=True, text=True)
    print(r.stdout[-400:], r.stderr[-400:])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

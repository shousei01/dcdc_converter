"""Rev D copper pours after routing.
1) Local power pours on F.Cu around each hot loop (switch nodes kept small, supply/return nodes generous).
2) Low-priority ground floods (F.Cu, In2.Cu, B.Cu) per isolation domain: GNDP primary, GND secondary, GND_ISO CAN.
Islands are removed, so a flood only survives where it touches its own net. Usage: pours.py in out"""
import sys
import pcbnew

sys.path.insert(0, "/home/claude/dcdc")
import gen_pcb3 as GP

mm = pcbnew.FromMM
F, B, I2 = pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In2_Cu
R = lambda x0, y0, x1, y1: [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]

# (net, layer, polygon, priority, clearance)
POURS = [
    # LLC primary
    ("HB_SW", F, R(52.6, 31.4, 60.2, 44.6), 30, 0.3),
    ("CR_MID", F, R(54.6, 14.0, 60.2, 29.8), 30, 0.3),
    ("VIN", F, [(37.0, 31.0), (52.4, 31.0), (52.4, 37.3), (37.0, 37.3)], 25, 0.3),
    ("GNDP", F, R(37.0, 38.7, 50.2, 46.4), 25, 0.3),
    # synchronous rectifier
    ("SR_D2", F, R(79.8, 15.8, 89.3, 23.6), 30, 0.3),
    ("SR_D1", F, R(79.8, 36.4, 89.3, 44.2), 30, 0.3),
    ("VBUS", F, R(79.8, 24.0, 88.4, 36.0), 28, 0.3),
    ("GND", F, R(89.3, 16.5, 91.9, 43.5), 26, 0.3),
    # 4SBB input
    ("VBUS", F, [(94.8, 20.2), (107.4, 20.2), (107.4, 26.7), (102.5, 26.7), (102.5, 23.85), (94.8, 23.85)], 28, 0.3),
    ("GND", F, R(94.8, 24.6, 102.3, 28.2), 26, 0.3),
    ("SW1", F, R(107.5, 12.6, 116.3, 33.4), 30, 0.3),
    ("SW2", F, R(127.7, 12.6, 136.7, 33.4), 30, 0.3),
    ("PGND", F, [(107.5, 33.5), (136.8, 33.5), (136.8, 36.4), (120.7, 36.4), (120.7, 39.8), (117.4, 39.8), (117.4, 36.4), (107.5, 36.4)], 28, 0.3),
    # 4SBB output
    ("VOUT", F, [(136.7, 19.4), (158.6, 19.4), (158.6, 22.35), (141.4, 22.35), (141.4, 24.4), (136.7, 24.4)], 28, 0.3),
    ("GND", F, R(141.9, 24.65, 158.6, 28.0), 26, 0.3),
]
# ground floods per domain (all copper layers except In1 which already carries the planes)
e = 0.6
DOMAINS = [
    ("GNDP", [(e, e), (GP.XB - GP.BAND, e), (GP.XB - GP.BAND, GP.H - e), (e, GP.H - e)]),
    ("GND", [(GP.XB + GP.BAND, e), (GP.W - e, e), (GP.W - e, GP.YC - GP.BAND), (GP.XC - GP.BAND, GP.YC - GP.BAND),
             (GP.XC - GP.BAND, GP.H - e), (GP.XB + GP.BAND, GP.H - e)]),
    ("GND_ISO", [(GP.XC + GP.BAND, GP.YC + GP.BAND), (GP.W - e, GP.YC + GP.BAND), (GP.W - e, GP.H - e), (GP.XC + GP.BAND, GP.H - e)]),
]


def zone(b, net, layer, poly, prio, clr, name):
    z = pcbnew.ZONE(b)
    z.SetLayer(layer)
    z.SetNet(b.FindNet(net))
    ol = z.Outline()
    ol.NewOutline()
    for x, y in poly:
        ol.Append(mm(x), mm(y))
    z.SetLocalClearance(mm(clr))
    z.SetMinThickness(mm(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)
    z.SetThermalReliefGap(mm(0.3))
    z.SetThermalReliefSpokeWidth(mm(0.5))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    z.SetAssignedPriority(prio)
    z.SetZoneName(name)
    b.Add(z)
    return z


def main(src, dst):
    b = pcbnew.LoadBoard(src)
    for i, (net, layer, poly, prio, clr) in enumerate(POURS):
        zone(b, net, layer, poly, prio, clr, f"PWR_{net}_{i}")
    for net, poly in DOMAINS:
        for layer in (F, I2, B):
            zone(b, net, layer, poly, 1, 0.3, f"FLOOD_{net}")
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(dst, b)
    print("zones", len(list(b.Zones())))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

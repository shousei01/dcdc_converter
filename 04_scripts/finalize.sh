#!/bin/bash
# finalize.sh <routed.kicad_pcb> -> pcb4/final.kicad_pcb + DRC report
set -e
cd /home/claude/dcdc
python3 - "$1" <<'PY' 2>/dev/null
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
ds = b.GetDesignSettings()
ds.m_CopperEdgeClearance = pcbnew.FromMM(0.3)     # JLCPCB routed-edge minimum
pcbnew.SaveBoard("/tmp/f0.kicad_pcb", b)
PY
python3 pours.py /tmp/f0.kicad_pcb /tmp/f1.kicad_pcb 2>/dev/null | grep zones
python3 silk_fix.py /tmp/f1.kicad_pcb pcb4/final.kicad_pcb 2>/dev/null | tail -1
python3 - <<'PY' 2>/dev/null
import pcbnew, re, collections
b = pcbnew.LoadBoard("/home/claude/dcdc/pcb4/final.kicad_pcb")
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard("/home/claude/dcdc/pcb4/final.kicad_pcb", b)
pcbnew.WriteDRCReport(b, "/home/claude/dcdc/pcb4/drc_final.rpt", pcbnew.EDA_UNITS_MILLIMETRES, True)
t = open("/home/claude/dcdc/pcb4/drc_final.rpt").read()
print(collections.Counter(re.findall(r"^\[(\w+)\]", t, re.M)))
print("tracks", sum(1 for x in b.GetTracks() if x.Type() != pcbnew.PCB_VIA_T), "vias", sum(1 for x in b.GetTracks() if x.Type() == pcbnew.PCB_VIA_T))
PY

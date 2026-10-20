#!/bin/bash
# drc5.sh board.kicad_pcb [report] : run KiCad DRC with the JLC rules, print counts by type
B=$1; R=${2:-/tmp/claude-0/dr5/drc.rpt}
cp $B /tmp/claude-0/dr5/DCDC_LLC_4SBB_G474.kicad_pcb
cp /home/claude/dcdc/pcb5/DCDC_LLC_4SBB_G474.kicad_dru /tmp/claude-0/dr5/
python3 - "$R" <<'PY'
import sys, pcbnew, re, collections
b = pcbnew.LoadBoard("/tmp/claude-0/dr5/DCDC_LLC_4SBB_G474.kicad_pcb")
pcbnew.WriteDRCReport(b, sys.argv[1], pcbnew.EDA_UNITS_MILLIMETRES, True)
t = open(sys.argv[1]).read()
print(collections.Counter(re.findall(r"^\[(\w+)\]", t, re.M)))
PY

#!/bin/bash
# build.sh tag : pre-routed p3b -> route -> clean -> floods/stitch -> island vias -> clean -> DRC summary
set -e
cd /home/claude/dcdc
T=$1
timeout 3000 python3 pcb5/route5.py pcb5/p3b.kicad_pcb pcb5/r$T.kicad_pcb 40 > pcb5/r$T.out 2>&1
python3 opt/dangling.py pcb5/r$T.kicad_pcb pcb5/r${T}c.kicad_pcb 2>&1 | grep -v leak | tail -1
python3 pcb5/finish5.py pcb5/r${T}c.kicad_pcb pcb5/f$T.kicad_pcb 2>&1 | grep -v leak | tail -2
python3 pcb5/islands5.py pcb5/f$T.kicad_pcb pcb5/f${T}i.kicad_pcb 2>&1 | grep -v leak | grep -v "  via"
python3 opt/dangling.py pcb5/f${T}i.kicad_pcb pcb5/f${T}d.kicad_pcb 2>&1 | grep -v leak | tail -1
./pcb5/drc5.sh pcb5/f${T}d.kicad_pcb /tmp/claude-0/dr5/f${T}d.rpt | tail -1
python3 pcb5/uncon.py /tmp/claude-0/dr5/f${T}d.rpt 8

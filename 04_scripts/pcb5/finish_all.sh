#!/bin/bash
# finish_all.sh routed.kicad_pcb tag : clean -> floods/stitch -> island vias -> clean -> DRC summary
set -e
cd /home/claude/dcdc
S=$1; T=$2
python3 opt/dangling.py $S pcb5/${T}c.kicad_pcb 2>&1 | grep -v leak | tail -1
python3 pcb5/finish5.py pcb5/${T}c.kicad_pcb pcb5/${T}f.kicad_pcb 2>&1 | grep -v leak | tail -2
python3 pcb5/islands5.py pcb5/${T}f.kicad_pcb pcb5/${T}i.kicad_pcb 2>&1 | grep -v leak | grep -v "  via"
python3 opt/dangling.py pcb5/${T}i.kicad_pcb pcb5/${T}d.kicad_pcb 2>&1 | grep -v leak | tail -1
./pcb5/drc5.sh pcb5/${T}d.kicad_pcb /tmp/claude-0/dr5/${T}d.rpt | tail -1
python3 pcb5/uncon.py /tmp/claude-0/dr5/${T}d.rpt 8

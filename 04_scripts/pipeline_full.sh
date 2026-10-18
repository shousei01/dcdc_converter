#!/bin/bash
set -e
cd /home/claude/dcdc
./pipeline4.sh
./pipeline4b.sh
timeout 2400 python3 fix_unconnected.py pcb4/r2.kicad_pcb pcb4/r3.kicad_pcb | tail -2
timeout 3000 python3 -u maze.py pcb4/r3.kicad_pcb pcb4/r5.kicad_pcb | grep -E "start|end|NO PATH|DRC FAIL"
cp pcb4/r5.kicad_pcb /tmp/c0.kicad_pcb; for i in 1 2 3; do python3 cleanup.py /tmp/c0.kicad_pcb /tmp/c1.kicad_pcb | grep removed; cp /tmp/c1.kicad_pcb /tmp/c0.kicad_pcb; done; cp /tmp/c0.kicad_pcb pcb4/r6.kicad_pcb
timeout 1500 python3 -u m15.py pcb4/r6.kicad_pcb pcb4/r8.kicad_pcb | grep -E "start|end|NO PATH|DRC FAIL"
echo FULL_DONE

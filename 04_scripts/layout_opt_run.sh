#!/bin/bash
set -e
cd /home/claude/dcdc
python3 opt/opt1.py opt/base.kicad_pcb opt/o1.kicad_pcb 2>&1 | grep -v leak || true
python3 opt/straighten.py opt/o1.kicad_pcb opt/o2.kicad_pcb 2>&1 | grep -v leak | tail -1
cp opt/o2.kicad_pcb opt/o3.kicad_pcb
for i in 1 2 3 4; do python3 opt/dangling.py opt/o3.kicad_pcb opt/o3.kicad_pcb 2>&1 | grep -v leak || true; done
python3 opt/stitch.py opt/o3.kicad_pcb opt/o4.kicad_pcb 2>&1 | grep -v leak | tail -1
python3 -c "
import sys,re,collections,pcbnew;sys.path.insert(0,'.');from fix_unconnected import drc
b=pcbnew.LoadBoard('opt/o4.kicad_pcb');print(drc(b,'/tmp/claude-0/d.rpt'));print(collections.Counter(re.findall(r'^\[(\w+)\]',open('/tmp/claude-0/d.rpt').read(),re.M)))"

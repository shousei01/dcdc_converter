#!/bin/bash
# png.sh board.kicad_pcb "F.Cu,F.SilkS,Edge.Cuts" out.png [dpi] [clip x0,y0,x1,y1 in mm]
B=$1; L=$2; O=$3; DPI=${4:-150}; CLIP=${5:-}
T=$(mktemp -d /tmp/claude-0/-home-claude/cb583e8c-a60d-5a31-af5a-8379480738ac/scratchpad/png.XXXX)
kicad-cli pcb export pdf -o $T/p.pdf --layers "$L" $B >/dev/null 2>&1
python3 - "$T/p.pdf" "$O" "$DPI" "$CLIP" <<'PY'
import sys, pymupdf as f
d=f.open(sys.argv[1]); p=d[0]
# find board drawing bbox: use drawings extents
s=72/25.4
r=f.Rect(-1*s,-1*s,161*s,106*s)
clip=r
if sys.argv[4]:
    x0,y0,x1,y1=[float(v) for v in sys.argv[4].split(',')]
    clip=f.Rect(x0*s, y0*s, x1*s, y1*s)
p.get_pixmap(dpi=int(sys.argv[3]), clip=clip).save(sys.argv[2])
print(clip)
PY

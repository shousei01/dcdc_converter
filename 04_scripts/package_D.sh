#!/bin/bash
# Usage: package.sh <final routed board>
set -e
cd /home/claude/dcdc
SRC=$1
N=DCDC_LLC_4SBB_G474
OUT=/home/claude/dcdc/release_D
rm -rf $OUT; mkdir -p $OUT/$N/custom_fp.pretty $OUT/gerbers
cp sch3/*.kicad_sch $OUT/$N/
cp out/custom.kicad_sym $OUT/$N/
cp out/custom_fp.pretty/*.kicad_mod $OUT/$N/custom_fp.pretty/
printf '(sym_lib_table\n  (lib (name "custom")(type "KiCad")(uri "${KIPRJMOD}/custom.kicad_sym")(options "")(descr "UCC27211, UCC27524, CA-IS3062VW, CA-IS3642LVW"))\n)\n' > $OUT/$N/sym-lib-table
printf '(fp_lib_table\n  (lib (name "custom_fp")(type "KiCad")(uri "${KIPRJMOD}/custom_fp.pretty")(options "")(descr "PQ2620 transformer (Rev D pin pitch), programming pads"))\n)\n' > $OUT/$N/fp-lib-table
cp $SRC $OUT/$N/$N.kicad_pcb
cat > $OUT/$N/$N.kicad_pro <<EOF
{
  "board": {"design_settings": {"defaults": {}, "rules": {"min_clearance": 0.2, "min_track_width": 0.2}}, "layer_presets": []},
  "boards": [],
  "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
  "meta": {"filename": "$N.kicad_pro", "version": 1},
  "pcbnew": {"last_paths": {}, "page_layout_descr_file": ""},
  "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
  "sheets": [],
  "text_variables": {}
}
EOF
# outputs
kicad-cli sch export pdf -o $OUT/${N}_schematic.pdf $OUT/$N/$N.kicad_sch >/dev/null
kicad-cli sch export netlist --format kicadxml -o /tmp/final_net.xml $OUT/$N/$N.kicad_sch >/dev/null
python3 verify.py /tmp/final_net.xml
kicad-cli pcb export gerbers -o $OUT/gerbers/ --layers "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts" --subtract-soldermask $OUT/$N/$N.kicad_pcb >/dev/null
kicad-cli pcb export drill -o $OUT/gerbers/ --format excellon --excellon-separate-th $OUT/$N/$N.kicad_pcb >/dev/null
kicad-cli pcb export pos -o $OUT/${N}_CPL.csv --format csv --units mm --side both $OUT/$N/$N.kicad_pcb >/dev/null
( cd $OUT/gerbers && python3 -c "
import zipfile,os
z=zipfile.ZipFile('../${N}_gerbers_JLCPCB.zip','w',zipfile.ZIP_DEFLATED)
[z.write(f) for f in sorted(os.listdir('.'))]; z.close()" )
for L in "F.Cu,F.SilkS,Edge.Cuts" "In1.Cu,Edge.Cuts" "In2.Cu,Edge.Cuts" "B.Cu,B.SilkS,Edge.Cuts"; do
  tag=$(echo $L | cut -d, -f1 | tr . _)
  kicad-cli pcb export pdf --layers "$L" -o /tmp/pcb_$tag.pdf $OUT/$N/$N.kicad_pcb >/dev/null
done
python3 -c "
import pymupdf as f
out=f.open()
for t in ['F_Cu','In1_Cu','In2_Cu','B_Cu']:
    out.insert_pdf(f.open(f'/tmp/pcb_{t}.pdf'))
out.save('$OUT/${N}_PCB_layers.pdf')"
cp out/BOM_DCDC_4SBB_G474.csv $OUT/BOM_${N}.csv
cp out/BOM_JLCPCB.csv $OUT/BOM_JLCPCB_${N}.csv
( cd $OUT && python3 -c "
import zipfile,os
z=zipfile.ZipFile('${N}_EasyEDA_import.zip','w',zipfile.ZIP_DEFLATED)
for r,_,fs in os.walk('$N'):
    for f in fs: z.write(os.path.join(r,f))
z.close()" )
ls -la $OUT
cp out_revD/pin-map.xlsx $OUT/

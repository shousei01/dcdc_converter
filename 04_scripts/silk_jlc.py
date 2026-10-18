"""JLC silkscreen: every reference to 1.0 mm / 0.15 mm stroke, kept where it was; only references that then
collide are re-placed (positions from silk_fix_jlc), iterated until the silkscreen DRC is clean.
usage: silk_jlc.py in.kicad_pcb out.kicad_pcb projdir"""
import sys,re,shutil,subprocess,pcbnew
sys.path.insert(0,'/home/claude/dcdc');from fix_unconnected import drc
mm=pcbnew.FromMM;M=pcbnew.ToMM
src,dst,pdir=sys.argv[1:4]
tmp=pdir+'/DCDC_LLC_4SBB_G474.kicad_pcb'
b=pcbnew.LoadBoard(src)
for f in b.GetFootprints():
    t=f.Reference()
    if t.GetLayer()==pcbnew.F_SilkS:
        t.SetTextSize(pcbnew.VECTOR2I(mm(1.0),mm(1.0)));t.SetTextThickness(mm(0.15))
b.Save(tmp)
subprocess.run(['python3','/home/claude/dcdc/opt/silk_fix_jlc.py',tmp,'/tmp/claude-0/silk_all.kicad_pcb'],capture_output=True)
alt=pcbnew.LoadBoard('/tmp/claude-0/silk_all.kicad_pcb')
moved=set()
for it in range(8):
    b=pcbnew.LoadBoard(tmp)
    drc(b,'/tmp/claude-0/silk.rpt');t=open('/tmp/claude-0/silk.rpt').read()
    refs=set()
    for blk in re.split(r'\n(?=\[)',t):
        if blk.startswith('[silk') or blk.startswith('[text'):
            refs|=set(re.findall(r"Reference '([^']+)'",blk))
    print('round',it,'conflicts',sorted(refs))
    new=refs-moved
    if not refs: break
    if not new: new=refs   # already moved but still colliding -> hide
    for r in new:
        f=b.FindFootprintByReference(r);g=alt.FindFootprintByReference(r)
        if r in moved:
            f.Reference().SetVisible(False); print('  hide',r); continue
        u=g.Reference();t_=f.Reference()
        t_.SetPosition(u.GetPosition());t_.SetTextAngle(u.GetTextAngle());t_.SetVisible(u.IsVisible())
        t_.SetHorizJustify(u.GetHorizJustify());t_.SetVertJustify(u.GetVertJustify())
        moved.add(r)
    b.Save(tmp)
shutil.copy(tmp,dst)
b=pcbnew.LoadBoard(dst)
print('hidden refs:',sorted(f.GetReference() for f in b.GetFootprints() if not f.Reference().IsVisible()))

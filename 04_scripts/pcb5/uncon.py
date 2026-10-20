"""summarise a DRC report: unconnected items by net with locations, clearance items. usage: uncon.py report"""
import re, sys, collections
t = open(sys.argv[1]).read()
blocks = re.split(r"\n(?=\[)", t)
by = collections.defaultdict(list)
cl = []
for bl in blocks:
    m = re.match(r"\[(\w+)\]", bl)
    if not m: continue
    k = m.group(1)
    items = re.findall(r"@\(([\d.]+) mm, ([\d.]+) mm\): (.*)", bl)
    if k == "unconnected_items":
        nets = re.findall(r"\[([^\]]+)\]", " ".join(i[2] for i in items))
        n = nets[0] if nets else "?"
        by[n].append(" | ".join(f"({float(x):.1f},{float(y):.1f}) {d[:60]}" for x, y, d in items))
    elif k in ("clearance", "shorting_items", "tracks_crossing", "via_dangling", "track_dangling", "hole_clearance", "copper_edge_clearance"):
        cl.append(k + ": " + bl.split("\n")[0][len(k)+2:][:80] + "\n    " + "\n    ".join(f"({float(x):.1f},{float(y):.1f}) {d[:70]}" for x, y, d in items))
for n, l in sorted(by.items(), key=lambda kv: -len(kv[1])):
    print(f"== {n}: {len(l)}")
    for s in l[: int(sys.argv[2]) if len(sys.argv) > 2 else 4]:
        print("   ", s)
print()
for c in cl: print(c)

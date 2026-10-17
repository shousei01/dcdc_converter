"""4SBB sizing v2: per-position FETs and LM5175-style buck-boost transition.
Q1 = input high side (hard-switch in buck)      -> NCEP0140AG
Q2 = input low side (sync rect in buck)         -> NCEP0160AG
Q3 = output high side (static-on in buck, SR in boost) -> NCEP0160AG
Q4 = output low side (hard-switch in boost)     -> NCEP0140AG
"""
import itertools, json, math, sys
F140 = dict(rds=23e-3*1.4, qg=26e-9, coss=139e-12, qrr=50e-9)   # max Rds @25C x1.4 hot
F160 = dict(rds=8.5e-3*1.4, qg=65e-9, coss=450e-12, qrr=80e-9)  # coss/qrr assumed (not on listing)
Q = {1: F140, 2: F160, 3: F160, 4: F140}
FSW = float(sys.argv[1]) if len(sys.argv) > 1 else 200e3
L = float(sys.argv[2]) if len(sys.argv) > 2 else 15e-6
DCR, TDEAD, VSD, VDRV = 25e-3, 30e-9, 0.85, 10.0
TOV = 8e-9          # V-I overlap per edge: Qgd 3.8 nC / ~1 A plateau current + Qgs2
RS, RSH_OUT, RSH_IN, PQ = 4e-3, 10e-3, 0.0, 0.7
PMAX, IMAX = 50.0, 5.0

def hard(v, i):   # hard-switched leg: turn-on + turn-off overlap
    return v * i * TOV * FSW

def point(vin, vout):
    iout = min(IMAX, PMAX / vout); pout = vout * iout
    if vout <= 0.85 * vin: m = "buck"
    elif vout >= vin / 0.85: m = "boost"
    else: m = "transition"
    eta = 0.95
    for _ in range(30):
        iin = pout / eta / vin
        if m == "buck":
            D = vout / vin / eta**0.3; Db = 0.0
            il = iout; dI = vout * (1 - D) / (L * FSW)
        elif m == "boost":
            D = 1.0; Db = 1 - vin * eta**0.3 / vout
            il = iout / (1 - Db); dI = vin * Db / (L * FSW)
        else:
            Db = max(0.10, 1 - 0.85 * vin / vout)          # boost leg at small duty
            D = vout * (1 - Db) / vin                       # buck-leg duty
            il = iout / (1 - Db)
            dI = max(abs(vin - vout/(1)) * min(D, 1 - Db) / (L * FSW), vin * Db / (L * FSW))
        irms = math.sqrt(il**2 + dI**2 / 12)
        cond = irms**2 * (Q[1]["rds"] * D + Q[2]["rds"] * (1 - D) + Q[4]["rds"] * Db + Q[3]["rds"] * (1 - Db))
        sw = 0.0
        if D < 1:   # input leg switching
            sw += hard(vin, il) + 0.5 * (Q[1]["coss"] + Q[2]["coss"]) * vin**2 * FSW \
                  + Q[2]["qrr"] * vin * FSW + VSD * il * 2 * TDEAD * FSW
        if Db > 0:  # output leg switching
            sw += hard(vout, il) + 0.5 * (Q[3]["coss"] + Q[4]["coss"]) * vout**2 * FSW \
                  + Q[3]["qrr"] * vout * FSW + VSD * il * 2 * TDEAD * FSW
        gate = (Q[1]["qg"] + Q[2]["qg"]) * VDRV * FSW * (D < 1) + (Q[3]["qg"] + Q[4]["qg"]) * VDRV * FSW * (Db > 0)
        gate /= 0.85
        pl = irms**2 * DCR + 0.12 * (dI / 3.0)**2 + 0.05
        i_rs = irms * math.sqrt(max(1 - D, 0) + Db)          # low-side conduction share
        ps = i_rs**2 * RS + iout**2 * RSH_OUT + iin**2 * RSH_IN
        loss = cond + sw + gate + pl + ps + PQ
        new = pout / (pout + loss)
        if abs(new - eta) < 1e-6: break
        eta = new
    # per-FET loss (for thermal): conduction share + switching attributed to hard-switch FET
    pf = {1: irms**2*Q[1]["rds"]*D, 2: irms**2*Q[2]["rds"]*(1-D), 3: irms**2*Q[3]["rds"]*(1-Db), 4: irms**2*Q[4]["rds"]*Db}
    if D < 1: pf[1] += hard(vin, il) + Q[2]["qrr"]*vin*FSW + 0.5*(Q[1]["coss"]+Q[2]["coss"])*vin**2*FSW; pf[2] += VSD*il*2*TDEAD*FSW
    if Db > 0: pf[4] += hard(vout, il) + Q[3]["qrr"]*vout*FSW + 0.5*(Q[3]["coss"]+Q[4]["coss"])*vout**2*FSW; pf[3] += VSD*il*2*TDEAD*FSW
    return dict(vin=vin, vout=vout, iout=round(iout,2), pout=round(pout,1), mode=m, D=round(D,3), Db=round(Db,3),
                il=round(il,2), dI=round(dI,2), ipk=round(il+dI/2,2), irms=round(irms,2),
                pQ1=round(pf[1],2), pQ2=round(pf[2],2), pQ3=round(pf[3],2), pQ4=round(pf[4],2),
                pL=round(pl,2), loss=round(loss,2), eta=round(eta,4), ton_ns=round(D/FSW*1e9))

if __name__ == "__main__":
    rows = [point(a, b) for a, b in itertools.product([12,18,24,36,48],[1.5,3.3,5,8,10,12,15,20,24,28,36,42,48])]
    hdr = list(rows[0].keys())
    if "-q" not in sys.argv:
        print("\t".join(hdr))
        for r in rows: print("\t".join(str(r[h]) for h in hdr))
    for k in ["ipk","irms","loss","pQ1","pQ2","pQ3","pQ4"]:
        w = max(rows, key=lambda r: r[k]); print(f"max {k:5s}= {w[k]:6}  @ {w['vin']}V->{w['vout']}V {w['mode']}")
    full = [r for r in rows if r["pout"] >= 49]
    print("min eta at 50 W:", min(r["eta"] for r in full), " min buck ton ns:", min(r["ton_ns"] for r in rows if r["mode"]=="buck"))
    json.dump(rows, open(f"grid_{int(FSW/1e3)}k_{int(L*1e6)}u.json","w"), indent=1)

"""Rev D part change check (18 Oct 2026): F1 -> 1206 7 A 63 V chip fuse, L2/L3 -> 5040 shielded 47 uH.
Checks the aux buck inductors (LMR16006X, 700 kHz, 10 V out) and the input fuse current margin."""
F_SW, VOUT, L = 700e3, 10.0, 47e-6          # LMR16006X fixed 0.7 MHz, 10 V rails
L_ISAT, L_IRMS, L_DCR = 1.1, 1.0, 0.354     # SWPA5040S470MT (LCSC C86617) listing
# 10 V rail loads (estimates): primary = U10 gate drive + U14 -> U12 isolator; secondary = U2/U3/U11 + U5 -> CAN
QG_PRI, F_LLC = 65e-9, 205e3                 # NCEP0160AG Qg, 2 FETs at the LLC frequency
I_PRI = 2 * QG_PRI * F_LLC + 0.6 / 5.0       # gate drive + isolator 0.6 W from the 5 V LDO
QG_SEC, F_SBB = 26e-9 * 2 + 65e-9 * 2, 150e3 # 4SBB: 2x NCEP0140 + 2x NCEP0160
I_SEC = QG_SEC * F_SBB + 0.03 + 0.07   # + SR driver / quiescent ~30 mA + CAN VCC ~70 mA
out = []
for name, iload in (("L3 primary aux", I_PRI), ("L2 secondary aux", I_SEC)):
    for vin in (12.0, 24.0, 48.0, 50.3):
        d = VOUT / vin
        di = VOUT * (1 - d) / (L * F_SW)
        ipk = iload + di / 2
        out.append(f"{name}: VIN {vin:4.1f} V  load {iload*1e3:5.0f} mA  ripple {di*1e3:4.0f} mA pp  "
                   f"peak {ipk*1e3:4.0f} mA (Isat {L_ISAT} A, margin {L_ISAT/ipk:4.1f}x)  DCR loss {iload**2*L_DCR*1e3:4.1f} mW")
# input fuse: worst case is 12 V in at full 50 W
FUSE_I, FUSE_V, DERATE = 7.0, 63.0, 0.75      # Littelfuse 0458007.DR; 75 % continuous at 25 C
for vin, eff in ((12.0, 0.869), (24.0, 0.914), (48.0, 0.918)):
    iin = 50.0 / eff / vin
    out.append(f"F1: VIN {vin:4.1f} V  input {iin:4.2f} A = {iin/FUSE_I*100:3.0f} % of 7 A "
               f"(limit {FUSE_I*DERATE:.2f} A at 25 C) {'OK' if iin <= FUSE_I*DERATE else 'OVER'}")
out.append(f"F1 voltage rating {FUSE_V:.0f} V > OVP trip 50.26 V; surges above 63 V are clamped by D1 SMBJ51A (82 V at 7.3 A)")
print("\n".join(out))
open("aux_fuse_check.txt", "w").write("\n".join(out) + "\n")

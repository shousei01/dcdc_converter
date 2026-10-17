"""LLC DCX (half-bridge, centre-tapped SR) feeding the 4SBB, 12-48 V in.
Np : Ns = 1 : 2 per half -> Vbus ~= Vin.  Fixed frequency at fr, 50% duty.
Bus power per Vin = worst-case 4SBB input power at that Vin (from grid_150k_22u.json).
"""
import json, math

grid = json.load(open("/home/claude/calc/grid_150k_22u.json"))
PQ_4SBB = 0.7          # housekeeping inside 4SBB loss figure (MCU, CAN, aux) - kept in Pbus

# --- tank and transformer
FS = 200e3             # switching frequency (= fr nominal)
LR = 1.0e-6            # resonant L = transformer leakage referred to primary
CR = 660e-9            # 2 x 330 nF split resonant caps (each 3 x 110 nF C0G -> use 3x100n+... see BOM)
LM = 50e-6             # magnetising inductance (gapped PQ2620)
NP, NS = 4, 8          # turns; Ns per half of the centre tap
AE, VE = 119e-6, 5470e-9   # PQ2620 Ae (m^2), Ve (m^3)
TD = 150e-9            # primary dead time
COSS_TR = 2 * 450e-12 + 100e-12   # two primary FETs (time-related) + winding capacitance
# --- devices
R_PRI = 8.5e-3 * 1.4   # NCEP0160AG, max Rds x hot factor
R_SR = 16e-3 * 1.4     # BSC160N15NS5
QG_PRI, QG_SR = 65e-9, 19e-9
R_CU_P, R_CU_S = 6e-3, 18e-3      # AC winding resistance, primary / each secondary half
R_CR_ESR = 5e-3


def core_loss(bpk, f):
    # TDK N97-like Steinmetz fit: Pv[kW/m^3] ~= 50 * (B/0.1T)^2.6 * (f/100k)^1.3 at 100 C
    return 50e3 * (bpk / 0.1) ** 2.6 * (f / 100e3) ** 1.3 * VE


fr = 1 / (2 * math.pi * math.sqrt(LR * CR))
z0 = math.sqrt(LR / CR)
n = NS / NP
print(f"fr = {fr/1e3:.1f} kHz, Z0 = {z0:.2f} ohm, Lm/Lr = {LM/LR:.0f}, n = {n}")
print(f"ZVS: Lm max for td {TD*1e9:.0f} ns = {TD/(8*COSS_TR*FS)*1e6:.0f} uH (chosen {LM*1e6:.0f} uH)")

rows = []
for vin in sorted({r["vin"] for r in grid}):
    pts = [r for r in grid if r["vin"] == vin]
    worst = max(pts, key=lambda r: r["pout"] + r["loss"])
    pbus = worst["pout"] + worst["loss"]
    vbus = vin * n / 2 * 0.985            # ~1.5% drop
    ibus = pbus / vbus
    ip_s = math.pi / 2 * ibus              # SR half-sine peak
    i_sr_rms = ip_s / 2
    ip_p = n * ip_s                        # primary load current peak
    im_pk = (vin / 2) / (4 * LM * FS)
    i_pri_rms = math.sqrt((ip_p / math.sqrt(2)) ** 2 + (im_pk / math.sqrt(3)) ** 2)
    p_pri = i_pri_rms ** 2 * R_PRI         # two FETs, each half the time
    p_off = 2 * 0.5 * vin * im_pk * 10e-9 * FS
    p_sr = 2 * i_sr_rms ** 2 * R_SR
    p_gate = (2 * QG_PRI + 2 * QG_SR) * 10 * FS / 0.85
    bpk = (vin / 2) / (4 * FS * NP * AE)
    p_core = core_loss(bpk, FS)
    p_cu = i_pri_rms ** 2 * R_CU_P + 2 * i_sr_rms ** 2 * R_CU_S
    p_cr = i_pri_rms ** 2 * R_CR_ESR
    loss = p_pri + p_off + p_sr + p_gate + p_core + p_cu + p_cr + 0.15   # +0.15 W primary aux/isolator
    eta_llc = pbus / (pbus + loss)
    vcr_pk = vin / 2 + ip_p / (2 * math.pi * FS * CR)
    zvs_ok = im_pk * TD >= COSS_TR * vin
    eta_tot = worst["pout"] / (pbus + loss)
    rows.append(dict(vin=vin, worst_out=f"{worst['vout']}V/{worst['iout']}A", pbus=round(pbus, 1),
                     ibus=round(ibus, 2), ipri_rms=round(i_pri_rms, 2), ipri_pk=round(ip_p + im_pk, 1),
                     isr_rms=round(i_sr_rms, 2), im_pk=round(im_pk, 2), p_pri=round(p_pri + p_off, 2),
                     p_sr=round(p_sr, 2), p_xfmr=round(p_core + p_cu, 2), p_core=round(p_core, 2),
                     loss_llc=round(loss, 2), eta_llc=round(eta_llc, 4), loss_4sbb=worst["loss"],
                     loss_total=round(loss + worst["loss"], 2), eta_total=round(eta_tot, 4),
                     bpk_mT=round(bpk * 1e3), vcr_pk=round(vcr_pk, 1), vsr_max=round(2 * vbus, 1), zvs=zvs_ok))

hdr = list(rows[0])
print("\t".join(hdr))
for r in rows:
    print("\t".join(str(r[h]) for h in hdr))
json.dump(rows, open("/home/claude/calc/llc_results.json", "w"), indent=1)

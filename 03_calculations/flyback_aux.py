"""Rev E isolated aux flyback (block K): operating points, stresses, clamp, feedback, rail budgets.
UC3843B, PA3855.006NLT (EP13, Lp 21 uH +/-10 %, Np:Ns 1.33:1, Llk 0.3 uH max, K1 583.3 G/A, Bpk < 2700 G),
FDN86246 (150 V), SS110 rectifier / clamp, R114 0.5 ohm, RT 10k / CT 1 nF, RCD clamp 4.7k / 4.7 nF.
Run: python3 flyback_aux.py > flyback_aux.txt
"""
import math

# ---------------------------------------------------------------- rail budget (secondary +10 V)
f_sbb, f_llc = 150e3, 205e3
qg = {"NCEP0140AG": 26e-9, "NCEP0160AG": 45e-9, "BSC160N15NS5": 19e-9, "FDN86246": 6e-9}
i_sbb = (2 * qg["NCEP0140AG"] + 2 * qg["NCEP0160AG"]) * f_sbb + 2 * 0.4e-3      # Q1..Q4 via U2/U3 + quiescent
i_sr = 2 * qg["BSC160N15NS5"] * f_llc + 1.0e-3                                   # Q7/Q8 via U11
i_5v = {"CA-IS3062VW (CAN + iso DC-DC), dominant worst": 0.120, "3.3 V LDO input": 0.0}
i_3v3 = {"STM32G474 170 MHz, ADC/HRTIM/FDCAN on": 0.045, "isolator U12 side B": 0.004, "CAN VCCL": 0.002,
         "LEDs D4/D5": 0.0026, "INA181 x2 + dividers + pull-ups": 0.0015}
I3 = sum(i_3v3.values())
i_5v["3.3 V LDO input"] = I3 + 0.0001
I5 = sum(i_5v.values())
eta_buck = 0.85
i_buck_in = I5 * 5.05 / 10.0 / eta_buck
I10 = i_sbb + i_sr + i_buck_in
P10 = I10 * 10.0

# primary +10V_P (U13, LMR16006, 0.6 A)
i_llc_drv = 2 * qg["NCEP0160AG"] * f_llc + 0.5e-3
i_uc3843 = 12e-3 + qg["FDN86246"] * 175e3      # onsemi UC3843B ICC typ 12 mA (17 mA max)
i_5vp = 0.004 + 0.0004 * 3 + 0.0025 + 0.002     # isolator side A, LMV331 x3, TL431 bias, ramp / pull-ups
I10P = i_llc_drv + i_uc3843 + i_5vp

print("=== Rail budget ===")
print(f"+3V3  : {I3*1e3:6.1f} mA  -> TLV75533 loss {(5.05-3.3)*I3*1e3:5.1f} mW")
print(f"+5V   : {I5*1e3:6.1f} mA  (buck U4 from +10 V, eta {eta_buck:.2f})")
print(f"+10V  : {I10*1e3:6.1f} mA = {P10:4.2f} W  [4SBB drivers {i_sbb*1e3:.1f} mA, SR driver {i_sr*1e3:.1f} mA, buck in {i_buck_in*1e3:.1f} mA]")
print(f"+10V_P: {I10P*1e3:6.1f} mA  [LLC driver {i_llc_drv*1e3:.1f} mA, UC3843 {i_uc3843*1e3:.1f} mA, 5V_P loads {i_5vp*1e3:.1f} mA]  (U13 rated 600 mA)")
print(f"U14 AMS1117-5 (primary) dissipation {(10-5)*i_5vp*1e3:.0f} mW")

# ---------------------------------------------------------------- flyback
Lp_nom, Lk, n, K1 = 21e-6, 0.3e-6, 1.33, 583.3
RT, CT = 10e3, 1e-9
f_typ = 1.72 / (RT * CT)           # TI formula; onsemi 1.8/(RT CT) = 180 kHz -> both covered below
Vout, Vf = 10.0, 0.6
Vr = (Vout + Vf) * n
Rcs, Vcs = 0.5, 1.0
Rds, Coss, tf = 0.25, 25e-12, 15e-9    # FDN86246 hot Rds, Coss, turn-off fall time (10 ohm gate, 1 A sink)
Rclamp, eta = 4.7e3, 0.80

print("\n=== Flyback operating points (DCM check: ton + treset < T) ===")
print(f"Vr (reflected) = {Vr:.1f} V,  f = {f_typ/1e3:.0f}-{1.8/(RT*CT)/1e3:.0f} kHz,  Ipk limit = {Vcs/Rcs:.2f} A")
print("Pout  Vin   Lp     Ipk    ton    trst   T      mode  D     Bpk[G] Irms_FET Pfet[mW] Vclamp Vds_max Vr_diode")
for pout in (P10, 3.0):
    for vin in (12, 24, 48, 50):
        for Lp, f in ((Lp_nom, f_typ), (Lp_nom * 0.9, 1.8 / (RT * CT))):
            pin = pout / eta
            ipk = math.sqrt(2 * pin / (Lp * f))
            ton, trst, T = Lp * ipk / vin, Lp * ipk / Vr, 1 / f
            D = ton / T
            irms = ipk * math.sqrt(D / 3)
            plk = 0.5 * Lk * ipk ** 2 * f
            # RCD: Vc^2/R = Plk * Vc/(Vc - Vr)  ->  Vc(Vc - Vr) = R*Plk
            vc = (Vr + math.sqrt(Vr ** 2 + 4 * Rclamp * plk)) / 2
            pfet = irms ** 2 * Rds + 0.5 * (vin + vc) * ipk * tf * f + 0.5 * Coss * vin ** 2 * f
            print(f"{pout:4.2f} {vin:4.0f}  {Lp*1e6:4.1f}u  {ipk:5.2f}  {ton*1e6:5.2f}u {trst*1e6:5.2f}u {T*1e6:5.2f}u "
                  f"{'DCM ' if ton + trst < T else 'CCM '} {D:5.2f} {K1*ipk:6.0f} {irms:7.3f}  {pfet*1e3:6.0f}   {vc:5.1f}  {vin+vc+5:5.1f}   {Vout + vin/n:5.1f}")
ipk_lim = Vcs / Rcs
print(f"Current limit: Ipk {ipk_lim:.2f} A -> Bpk {K1*ipk_lim:.0f} G (< 2700 G), "
      f"max input power ~{0.5*Lp_nom*ipk_lim**2*f_typ:.1f} W (DCM bound), FET 1.6 A cont / 6 A pulsed")
plk_lim = 0.5 * Lk * ipk_lim ** 2 * f_typ
vc_lim = (Vr + math.sqrt(Vr ** 2 + 4 * Rclamp * plk_lim)) / 2
print(f"At current limit: Vclamp {vc_lim:.1f} V, R116 {vc_lim**2/Rclamp*1e3:.0f} mW (1206, 250 mW), "
      f"Vds at 50 V in {50+vc_lim+5:.0f} V, at 82 V TVS clamp {82+vc_lim+5:.0f} V (FDN86246 150 V)")
print(f"Clamp RC time constant {Rclamp*4.7e-9*1e6:.0f} us >> T {1e6/f_typ:.1f} us")

# rectifier, output ripple
iout_max = 3.0 / Vout
pin3 = 3.0 / eta
ipk3 = math.sqrt(2 * pin3 / (Lp_nom * f_typ))
print(f"\nD9 SS110: Iavg {iout_max:.2f} A max ({I10:.2f} A typ), Ipk_sec {ipk3*n:.2f} A, Vr {Vout+50/n:.0f} V + ringing (100 V part), "
      f"Pd {0.6*iout_max*1e3:.0f} mW max")
c_eff = 2 * 10e-6 * 0.6
print(f"Output ripple (C96+C97 ~{c_eff*1e6:.0f} uF eff. at 10 V): {iout_max/f_typ/c_eff*1e3:.0f} mV p-p at 3 W, "
      f"{I10/f_typ/c_eff*1e3:.0f} mV at typ load (+ C24/C25 at the drivers)")
print(f"R114 sense: Irms {ipk3*math.sqrt((Lp_nom*ipk3/12*f_typ)/3):.2f} A -> {ipk3**2*(Lp_nom*ipk3/12*f_typ)/3*Rcs*1e3:.0f} mW at 12 V / 3 W")

# ---------------------------------------------------------------- feedback
Vref431, Rtop, Rbot = 2.495, 30e3, 10e3
print("\n=== Secondary regulation ===")
v = Vref431 * (1 + Rtop / Rbot)
print(f"+10V set point {v:.2f} V; with TL431A 1 % and 1 % resistors: {v*0.97:.2f} .. {v*1.03:.2f} V")
R117, R118, Vled = 1.5e3, 1.0e3, 1.1
for vka in (2.5, 3.0):
    itot = (Vout - vka - Vled) / R117
    print(f"  TL431 at Vka {vka} V: total {itot*1e3:.2f} mA, LED max {(itot - Vled/R118)*1e3:.2f} mA "
          f"(needed ~1.0-1.5 mA: UC3843B EA source 0.8 mA typ / CTR >= 1)")
print(f"  TL431 minimum cathode current from R118 alone {Vled/R118*1e3:.1f} mA (> 1 mA)")
print(f"  Compensation zero R121 4.7k / C99 100 nF: {1/(2*math.pi*4.7e3*100e-9):.0f} Hz; integrator 1/(2 pi Rtop C99) = "
      f"{1/(2*math.pi*Rtop*100e-9):.0f} Hz; verify crossover (target 0.5-2 kHz) with a 50-100 % load step on the bench")
print("  Opto EL357N(B): CTR 130-260 % (5 mA), 3.75 kVrms; transformer Hi-pot 2250 Vdc pri-sec (functional isolation,")
print("  same class as PoE magnetics); creepage on the PCB >= 6 mm under T2/U21 by layout.")

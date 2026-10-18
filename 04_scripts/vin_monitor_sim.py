# behavioral sim of the VIN monitor: old (R110 feedback into ramp) vs new (feedback into OVP_DIV)
import numpy as np
VREF=2.495; V5=5.0; C=47e-9; I0=(5-(5*15/25+0.65))/56e3
R81,R82,R84=191e3,10e3,2.2e6
def run(vin,new,dt=2e-7,tres=20e-6):
    # returns t_high, period from one full cycle after settling
    v=0.0;out=None;t=0;edges=[];state=None
    Rfb = 4.7e6 if new else 1e6
    for cyc in range(3):
        v=0.0;t0=t
        while True:
            # comparator output: old: high while RAMPS>OVP ; new: high while RAMP<OVPeff
            if new:
                G=1/R81+1/R82+1/R84+1/Rfb
                vo_hi=(vin/R81+V5/Rfb)/G; vo_lo=(vin/R81)/G
                th = vo_hi if state in (None,1) else vo_lo
                s = 1 if v<th else 0
                iload=0
            else:
                ovp=(vin/R81)/(1/R81+1/R82+1/R84)
                vout = V5 if state==1 else 0.0
                vs = v+(vout-v)*10e3/(10e3+Rfb)
                s = 1 if vs>ovp else 0
                vout = V5 if s==1 else 0.0
                iload=(v-vout)/(10e3+Rfb)
            if s!=state: edges.append((t,s)); state=s
            v+= (I0-iload)/C*dt; t+=dt
            if v>=VREF: break
        # reset
        if new:
            if state!=1: edges.append((t,1)); state=1
        else:
            if state!=0: edges.append((t,0)); state=0
        t+=tres
    # measure last full cycle: period between rises
    rises=[e[0] for e in edges if e[1]==1]; falls=[e[0] for e in edges if e[1]==0]
    r1,r2=rises[-2],rises[-1]
    f=[x for x in falls if r1<x<r2][0]
    return f-r1, r2-r1
for new in (False,True):
    print('NEW' if new else 'OLD')
    res=[]
    for vin in (12,18,24,36,48):
        th,T=run(vin,new); Tr=T-20e-6
        x = (th-20e-6)/Tr if new else (Tr-th)/Tr
        res.append((vin,x))
    # best linear fit (2-point cal at 12 and 48) and ideal-formula error
    (v1,x1),(v2,x2)=res[0],res[-1]; a=(v2-v1)/(x2-x1); b=v1-a*x1
    for vin,x in res:
        nom = (50.47*x-0.203) if new else 50.37*x
        print(f' VIN {vin:4.1f}  x={x:.4f}  formula {nom:6.2f} V ({(nom-vin)/vin*100:+.2f}%)  2pt-cal {(a*x+b-vin)/vin*100:+.3f}%')

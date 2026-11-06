import sys, math, numpy as np, sympy as sp
sys.path.insert(0,'/home/johnjose/BrainGenix/wt/bec-dpend/src/models/double_pendulum')
import dp_env
from dp_env import Params, DoublePendulumEnv, DisturbanceCfg, dynamics
x,t1,t2,ph,xd,w1,w2,wp=sp.symbols('x t1 t2 ph xd w1 w2 wp')
mc,m1,m2,mb,l1,l2,Ls,g,I1,I2=sp.symbols('mc m1 m2 mb l1 l2 Ls g I1 I2')
q=sp.Matrix([x,t1,t2,ph]); qd=sp.Matrix([xd,w1,w2,wp])
def pos(*a): return sp.Matrix(a)
c1=pos(x+l1/2*sp.sin(t1),l1/2*sp.cos(t1))
c2=pos(x+l1*sp.sin(t1)+l2/2*sp.sin(t2),l1*sp.cos(t1)+l2/2*sp.cos(t2))
cb=pos(x+l1*sp.sin(t1)+l2*sp.sin(t2)+Ls*sp.sin(ph),l1*sp.cos(t1)+l2*sp.cos(t2)-Ls*sp.cos(ph))
T=mc*xd**2/2
for m,c,w,I in [(m1,c1,w1,I1),(m2,c2,w2,I2),(mb,cb,None,0)]:
    v=c.jacobian(q)*qd; T+=m*(v.T*v)[0]/2
    if w is not None: T+=I*w**2/2
V=g*(m1*c1[1]+m2*c2[1]+mb*cb[1])
M=sp.Matrix(4,4,lambda i,j: sp.diff(T,qd[i],qd[j]))
Mdot=sum((M.diff(q[k])*qd[k] for k in range(4)),sp.zeros(4,4))
dLdq=sp.Matrix([sp.diff(T-V,q[i]) for i in range(4)])
fM=sp.lambdify((x,t1,t2,ph,xd,w1,w2,wp,mc,m1,m2,mb,l1,l2,Ls,g,I1,I2),M,'numpy')
fR=sp.lambdify((x,t1,t2,ph,xd,w1,w2,wp,mc,m1,m2,mb,l1,l2,Ls,g,I1,I2),dLdq-Mdot*qd,'numpy')
MB=0.1; LS=0.3; BPH=0.0
def dyn8(s,F,p,tau1=0,tau2=0,mb_=MB):
    a=(*s,p.mc,p.m1,p.m2,mb_,p.l1,p.l2,LS,p.g,p.I1,p.I2)
    Mm=np.array(fM(*a),float); R=np.array(fR(*a),float).ravel()
    rel=s[6]-s[5]
    Q=np.array([F-p.bc*s[4], -p.bj1*s[5]+p.bj2*rel+tau1, -p.bj2*rel+tau2+BPH*(s[7]-s[6]), -BPH*(s[7]-s[6])])
    qdd=np.linalg.solve(Mm,R+Q)
    return np.concatenate([s[4:8],qdd])
def rk8(s,F,p,dt,t1_=0,t2_=0,mb_=MB):
    k1=dyn8(s,F,p,t1_,t2_,mb_);k2=dyn8(s+dt/2*k1,F,p,t1_,t2_,mb_);k3=dyn8(s+dt/2*k2,F,p,t1_,t2_,mb_);k4=dyn8(s+dt*k3,F,p,t1_,t2_,mb_)
    return s+dt/6*(k1+2*k2+2*k3+k4)
class BallEnv(DoublePendulumEnv):
    def __init__(s,*a,mb_=MB,**k): s.mb=mb_; super().__init__(*a,**k)
    def reset(s,s0=None):
        s0=np.zeros(8) if s0 is None else np.array(s0,float)
        r=super().reset(s0); return r
    def observe(s):
        o=np.array([s.s[0],s.s[1],s.s[2],s.s[4],s.s[5],s.s[6]])
        if s.dist is not None and any(s.dist.sensor_noise): o+=s.rng.normal(0,1,6)*np.asarray(s.dist.sensor_noise)
        return o
    def substep(s,F,external=True):
        F=max(-s.p.F_max,min(s.p.F_max,F))
        fe,a1,a2=s._disturbance() if external else (0,0,0)
        s.s=rk8(s.s,F+fe,s.p,s.dt,a1,a2,s.mb); s.t+=s.dt; return F
if __name__=='__main__':
    p=Params(); rng=np.random.default_rng(1)
    s6=rng.normal(0,.3,6); s8=np.array([s6[0],s6[1],s6[2],0.3,s6[3],s6[4],s6[5],0.0])
    a=dynamics(s6,2.0,p,0.01,0.01); b=dyn8(s8,2.0,p,0.01,0.01,mb_=1e-12)
    print(np.abs(a[3:]-b[4:7]).max(), np.abs(a[3:]-b[4:7]))

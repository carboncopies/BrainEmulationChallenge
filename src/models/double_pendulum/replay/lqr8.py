import numpy as np
from scipy.linalg import solve_discrete_are, expm
from ball import *
from dp_lqr import discretize
p=Params()
def lin8(mb_=MB,eps=1e-6):
    A=np.zeros((8,8))
    for i in range(8):
        e=np.zeros(8);e[i]=eps
        A[:,i]=(dyn8(e,0.0,p,0,0,mb_)-dyn8(-e,0.0,p,0,0,mb_))/(2*eps)
    B=((dyn8(np.zeros(8),eps,p,0,0,mb_)-dyn8(np.zeros(8),-eps,p,0,0,mb_))/(2*eps)).reshape(8,1)
    return A,B
def dlqr8(mb_=MB,h=0.01,Q=None,R=2.0):
    A,B=lin8(mb_)
    Q=np.diag([50,100,100,10,5,1,1,1.0]) if Q is None else Q
    Ad,Bd=expm(np.block([[A*h,B*h],[np.zeros((1,9))]]))[:8,:8],expm(np.block([[A*h,B*h],[np.zeros((1,9))]]))[:8,8:]
    P=solve_discrete_are(Ad,Bd,Q,np.array([[R]]))
    return np.linalg.solve(np.array([[R]])+Bd.T@P@Bd,Bd.T@P@Ad).ravel()
class Env8(BallEnv):
    def observe(s):
        o=s.s.copy()
        return np.array([o[0],o[1],o[2],o[3],o[4],o[5],o[6],o[7]])
def go8(ctrl,T,seed,mb_=MB,dist=True):
    env=Env8(None,0.005,0.01,1,DisturbanceCfg() if dist else None,None,seed,mb_=mb_)
    obs=env.reset([0,.0175,.0175,0,0,0,0,0]);S=[];F=[]
    for k in range(int(T/0.01)):
        obs,r=env.step(ctrl(obs)); S.append(r[-1][0]);F.append(r[-1][1])
        if env.failed(): break
    return np.array(S),np.array(F),len(S)<int(T/0.01)
if __name__=='__main__':
    K=dlqr8(); print(np.round(K,2))
    for seed in range(3):
        S,F,fell=go8(lambda o:float(-K@o),30,seed)
        print(seed,fell,len(S)*.01,np.degrees(np.abs(S[:,1:4]).max(0)).round(1),np.abs(S[:,0]).max().round(2),np.abs(F).max().round(1))

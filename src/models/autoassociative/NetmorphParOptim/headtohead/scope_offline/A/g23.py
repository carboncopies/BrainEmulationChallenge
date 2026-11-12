from g1 import *
from scipy.stats import nbinom
r1=json.load(open('g1_results.json')); a1=json.load(open('t1_results.json'))['cv']
out={'full':{}}; names=['const','log(n_pre*n_post)','logV','log dm.weight','days','log minsep']
models={}
for t in TG:
    y=df[t].values.astype(float); X=M1X(df,t); f=nbfit(X,y); al=f[2]
    # raw-scale coefficients: transform standardized params
    b=f[1][1:]/f[4]; c0=f[1][0]-(b*f[3]).sum(); st=np.append(c0,b)
    Z=sm.add_constant(X); g=sm.GLM(y,Z,family=sm.families.NegativeBinomial(alpha=al)).fit(start_params=st)
    out['full'][t]={'alpha_mle':float(al),'status':f[0],'coef':g.params.tolist(),'se_glm_alpha_fixed':g.bse.tolist(),'max_abs_diff_vs_mle':float(np.abs(g.params-st).max())}
    models[t]=(g.params,al)
# G2
comps=['raw_pyr_int_n','raw_int_pyr_n','raw_int_int_n']; P75={c:float(np.percentile(df[c],75)) for c in comps}
def J(d): return np.minimum.reduce([d[c]/P75[c] for c in comps]+[d['usable_conns2']/460])
df['J']=J(df); V=np.pi*df['shape.radius']**2*df['shape.thickness']; df['dens']=(df.pyramidal+df.interneuron)/(V*1e-9); pf=df.pyramidal/(df.pyramidal+df.interneuron)
df['clean']=(df.dens>=1e4)&(df.dens<=5e4)&(pf>=.7)&(pf<=.8)
q=lambda s:{k:float(v) for k,v in zip(['min','q25','med','q75','p90','max'],[s.min(),s.quantile(.25),s.median(),s.quantile(.75),s.quantile(.9),s.max()])}
out['P75']=P75; out['J_all']=q(df.J); out['J_clean']=dict(n=int(df.clean.sum()),**q(df.J[df.clean]))
cols=['pyramidal','interneuron','days','minneuronseparation','shape.radius','shape.thickness','dm.weight','raw_pyr_int_n','raw_int_pyr_n','raw_int_int_n','usable_conns2','J','dens','wall_s']
out['top_all']=df.sort_values('J',ascending=False).head(5)[cols].round(3).to_dict('records')
out['top_clean']=df[df.clean].sort_values('J',ascending=False).head(5)[cols].round(3).to_dict('records')
# G3
cf=[(70,30,113,50,1.0),(70,30,178,20,1.0),(70,30,141,32,1.0),(70,30,113,50,0.8),(70,18,106,50,1.0)]
G=[]
bA=np.array([-4.4642,1.7582,0.1119]) 
import json as j; t6=j.load(open('t5_results.json'))['t6']['A']['coef']
for k,(p,i,r,th,w) in enumerate(cf):
    d=pd.DataFrame([dict(days=25,pyramidal=p,interneuron=i,minneuronseparation=12,**{'shape.radius':r,'shape.thickness':th,'dm.weight':w})])
    row={'cfg':'abcde'[k],'config':dict(pyr=p,int=i,radius=r,thickness=th,dm=w)}
    mus={}
    for t in comps+['usable_conns2']:
        b,al=models[t]; mu=float(np.exp(np.append(1,M1X(d,t)[0])@b)); n=1/al; pp=1/(1+al*mu)
        row[t]={'mean':mu,'p10':int(nbinom.ppf(.1,n,pp)),'p90':int(nbinom.ppf(.9,n,pp))}; mus[t]=mu
    row['J_from_means']=float(min([mus[c]/P75[c] for c in comps]+[mus['usable_conns2']/460]))
    dens=(p+i)/(np.pi*r**2*th*1e-9); row['density']=float(dens); row['pyr_frac']=p/(p+i); row['soft_clean']=bool(1e4<=dens<=5e4 and .7<=p/(p+i)<=.8)
    row['wall_s_A']=float(np.exp(t6[0]+t6[1]*np.log(p+i)+t6[2]*25)); G.append(row)
out['G3']=G; json.dump(out,open('g23_results.json','w'),default=float,indent=1); print(json.dumps(out,indent=1))

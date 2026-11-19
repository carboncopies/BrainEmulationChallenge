"""Arbor means (to full precision) of the repro_g runs; uuid of each run's NetmorphOutput dir from its ExpsDB.json. usage: analyze_rep.py REP... -> rep_results.json (merged)"""
import sys,re,json,os,glob
sys.path.insert(0,'.'); import measure
OUT='/home/johnjose/BrainGenix/wt/linefix-instance/out/Admonishing/NetmorphOutput/'
T='V1n30_s31415_p0d0175_i0d0495'
A=(46234.6079,6681.5584,25736.7841,21022.7151); B=(47349.0650,6534.5135,25871.1473,21132.5274)
res=json.load(open('rep_results.json')) if os.path.exists('rep_results.json') else {}
for rep in sys.argv[1:]:
    gd='grow_%s_%s'%(T,rep); u=re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',open(gd+'/ExpsDB.json').read())[0]
    s=measure.summarize(OUT+u)
    v=(s['interneuron_axon']['len_mean'],s['interneuron_dendrite']['len_mean'],s['pyramidal_dendrite']['len_mean'],s['pyramidal_axon']['len_mean'])
    res[rep]=dict(dir=u,means=v,wall=open(gd+'/result.txt').read().split('wall=')[1].strip())
    cls=lambda ref:all(abs(a-b)<1e-6*abs(b) for a,b in zip(v,ref))
    print(rep,u,'%.4f %.4f %.4f %.4f'%v,'class A' if cls(A) else 'class B' if cls(B) else 'NEW (differs from A and B: ia %+.2f%% vs A, %+.2f%% vs B)'%(100*(v[0]/A[0]-1),100*(v[0]/B[0]-1)),flush=True)
json.dump(res,open('rep_results.json','w'),indent=1)

import json,glob,os,re
H='/home/johnjose/cos/netmorph_work/recipe_v2/option_B_scaled/'; R={}
for f in sorted(glob.glob(H+'raw_*ovl_*.json')):
    e=json.load(open(f)); n=os.path.basename(f)[4:-5]; s6=n.startswith('s629'); k=int(n.split('_')[2 if s6 else 1][1:])
    gj=json.load(open(H+('groups_ovl629_k%d.json' if s6 else 'groups_ovl_k%d.json')%k)); groups=[(g['members'],g['cue']) for g in gj['groups']]
    sh=set(groups[0][0])&set(groups[1][0]); allm={m for mm,_ in groups for m in mm}
    sp={int(a):b for a,b in e['spikes'].items()}; t=0; rows=[]
    for gi,(mem,cue) in enumerate(groups):
        for lab,sub in (('full',cue),('3a',cue[:3]),('3b',cue[1:])):
            t0=t; t+=500
            w=lambda i:[x for x in sp.get(i,[]) if t0<=x<t0+450]
            own_nc=[m for m in mem if m not in cue]
            own_fired=sum(1 for m in own_nc if w(m)); other_g=[m for g2,(mm,_) in enumerate(groups) if g2!=gi for m in mm if m not in mem]
            xt=sum(1 for m in other_g if w(m)); spur=sum(len(w(i)) for i in range(96) if i not in allm)
            shared_f=sum(1 for m in sh if m not in cue and w(m)); ints=sum(len(w(i)) for i in range(96,144))
            rows.append(dict(g=gi,ev=lab,own_nc_fired=own_fired,xtalk_cells=xt,spur_spikes=spur,shared_fired=shared_f,int_spikes=ints,last=max([x-t0 for i in range(96) for x in w(i)],default=0)))
    full=[r for r in rows if r['ev']=='full']; c3=[r for r in rows if r['ev']!='full']
    R[n]=dict(k=k,shared=sorted(sh),full_complete=[r['own_nc_fired'] for r in full],full_xtalk=[r['xtalk_cells'] for r in full],full_spur=sum(r['spur_spikes'] for r in full),
      full_int=sum(r['int_spikes'] for r in full),c3_false_own=sum(r['own_nc_fired'] for r in c3),c3_xtalk=sum(r['xtalk_cells'] for r in c3),c3_spur=sum(r['spur_spikes'] for r in c3),
      c3_shared_fired=sum(r['shared_fired'] for r in c3),last_full=max(r['last'] for r in full),rows=rows)
json.dump(R,open(H+'overlap_summary.json','w'),indent=0)
if __name__=='__main__':
    import sys
    print('tag'.ljust(20),'full_complete  xtalk(full)  spur  c3_false  c3_xtalk c3_spur int last')
    for n,r in R.items(): print(n.ljust(20),str(r['full_complete']).ljust(14),str(r['full_xtalk']).ljust(14),r['full_spur'],' ',r['c3_false_own'],' ',r['c3_xtalk'],' ',r['c3_spur'],r['full_int'],round(r['last_full'],1))

import json,sys,re
S=json.load(open('summary.json'))
def cell(n):
    s=S.get(n)
    if not s: return '   -   '
    rc=sum(s['complete']); 
    return ('%d/%d%s'%(s['spurious'],rc,'*' if s['success'] else ' ')).rjust(9)
for pre,cs in (('u_c',[0.15,0.2,0.3,0.4,0.45,0.5,0.55,0.6,0.65,0.7,0.75,0.8,0.85,0.9,1.0]),('s629_u_c',[0.15,0.5,0.55,0.6,0.65,0.7,0.75,0.8,0.9,1.0,1.5])):
    print(pre,'cell= spurious_nonmember_pyr_spikes/total_noncue_completions(16=all) ; * = ripple_success')
    print('c'.ljust(6),'SG'.rjust(9),'x1'.rjust(9),'s3g5'.rjust(9),'s5g5'.rjust(9),'s7g5'.rjust(9),'s10g5'.rjust(9),'s10g10'.rjust(9))
    for c in cs:
        print(str(c).ljust(6),cell(f'{pre}{c}_SG'),*[cell(f'{pre}{c}_{x}') for x in ('s1_g1','s3_g5','s5_g5','s7_g5','s10_g5','s10_g10')])

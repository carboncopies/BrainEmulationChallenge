"""Self-contained HTML report (no server, no external scripts): data embedded as JSON, grids embedded as log-quantised uint8 (base64).
Decoding in the page: q = 0 -> 0; else v = vmin * exp((q - 1) / 254 * ln(vmax / vmin)), vmin = vmax * 1e-4 (values below vmin show as vmin).
Full-precision grids are written next to the report as .npy files."""
import base64, json, html, numpy as np

def quantise(g):
    g = np.asarray(g, np.float64); vmax = float(g.max()) if g.size else 0.0
    if vmax <= 0: return dict(b64=base64.b64encode(np.zeros(g.size, np.uint8).tobytes()).decode(), vmin=0.0, vmax=0.0)
    vmin = vmax * 1e-4; flat = g.transpose(2, 1, 0).ravel()          # x fastest
    q = np.zeros(flat.size, np.uint8); nz = flat > 0
    q[nz] = np.clip(1 + np.round(254 * np.log(np.maximum(flat[nz], vmin) / vmin) / np.log(vmax / vmin)), 1, 255).astype(np.uint8)
    return dict(b64=base64.b64encode(q.tobytes()).decode(), vmin=vmin, vmax=vmax)

def dequantise(d, shape):
    q = np.frombuffer(base64.b64decode(d['b64']), np.uint8).astype(np.float64)
    v = np.where(q == 0, 0.0, d['vmin'] * np.exp((q - 1) / 254 * np.log(d['vmax'] / d['vmin'])) if d['vmax'] > 0 else 0.0)
    return v.reshape(shape[2], shape[1], shape[0]).transpose(2, 1, 0)

def write(path, models, profile, generated):
    payload = dict(generated=generated, profile=dict(name=profile['name'], description=profile.get('description', ''), path=profile.get('_path'), species=profile.get('species'), tissue=profile.get('tissue')), models=models)
    data = json.dumps(payload, separators=(',', ':'), default=lambda o: None).replace('</', '<\\/')
    open(path, 'w').write(PAGE.replace('/*DATA*/null', data))

PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Realism tester report</title>
<style>
:root{--bg:#fbfbfa;--fg:#1d1d1b;--mut:#6b6b66;--line:#deddd8;--card:#ffffff;--acc:#2f5f8a;--pass:#2e7d4f;--flag:#b3401f;--unk:#7a7a74;--info:#6c5a9c;--na:#9a9a94}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#171716;--fg:#e9e8e3;--mut:#a3a29c;--line:#34332f;--card:#1f1f1d;--acc:#8fb8de;--pass:#6fc28f;--flag:#ef8a6a;--unk:#a3a29c;--info:#b4a3e0;--na:#77766f}}
:root[data-theme="dark"]{--bg:#171716;--fg:#e9e8e3;--mut:#a3a29c;--line:#34332f;--card:#1f1f1d;--acc:#8fb8de;--pass:#6fc28f;--flag:#ef8a6a;--unk:#a3a29c;--info:#b4a3e0;--na:#77766f}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
header{padding:16px;border-bottom:1px solid var(--line);display:flex;flex-wrap:wrap;gap:12px;align-items:center}
h1{font-size:18px;margin:0 12px 0 0}h2{font-size:15px;margin:18px 0 8px}h3{font-size:14px;margin:14px 0 6px}
main{padding:0 16px 32px;max-width:1400px}select,button,input{font:inherit;color:inherit}
select,button{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:4px 8px}
nav{display:flex;flex-wrap:wrap;gap:4px;margin:12px 0}nav button.on{border-color:var(--acc);color:var(--acc)}
.mut{color:var(--mut)}.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px;margin:10px 0}
table{border-collapse:collapse;width:100%;font-size:13px}th,td{border-bottom:1px solid var(--line);padding:5px 6px;text-align:left;vertical-align:top}
th{font-weight:600;color:var(--mut);position:sticky;top:0;background:var(--card)}td.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.tw{overflow-x:auto;max-height:70vh}.badge{display:inline-block;padding:1px 7px;border-radius:9px;font-size:12px;font-weight:600;border:1px solid currentColor}
.pass{color:var(--pass)}.flag{color:var(--flag)}.unknown{color:var(--unk)}.info{color:var(--info)}.na{color:var(--na)}
.grid3{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}canvas{width:100%;height:auto;border:1px solid var(--line);border-radius:6px;background:#000;image-rendering:pixelated}
.row{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:6px 0}label{white-space:nowrap}input[type=range]{width:160px}
.sum span{margin-right:14px}pre{white-space:pre-wrap;word-break:break-word;font-size:12px}.small{font-size:12px}
#rad{background:var(--card)}
</style></head><body>
<header><h1>Realism tester</h1><label>Model <select id="msel"></select></label><span class="mut small" id="hdr"></span></header>
<main>
<nav id="tabs"></nav>
<section id="t_checks"></section><section id="t_heat" hidden></section><section id="t_radial" hidden></section><section id="t_all" hidden></section><section id="t_model" hidden></section>
</main>
<script>
const DATA=/*DATA*/null;
const $=s=>document.querySelector(s), esc=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function fmt(x){if(x==null||Number.isNaN(x))return '–';const a=Math.abs(x);if(a===0)return '0';if(a>=1e5||a<1e-3)return x.toExponential(2);if(a>=100)return x.toFixed(0);if(a>=10)return x.toFixed(1);return x.toFixed(3)}
const TABS=[['checks','Checks vs literature'],['heat','3D heat map'],['radial','Radial profile'],['all','All metrics'],['model','Model']];
let M=null, cache={};
function tabs(){const n=$('#tabs');n.innerHTML='';TABS.forEach(([k,l],i)=>{const b=document.createElement('button');b.textContent=l;b.onclick=()=>show(k);b.id='b_'+k;n.appendChild(b)});show('checks')}
function show(k){TABS.forEach(([t])=>{$('#t_'+t).hidden=t!==k;$('#b_'+t).classList.toggle('on',t===k)});if(k==='heat')drawHeat();if(k==='radial')drawRadial()}
const GROUPS=[['Cell-type proportions','proportion'],['Cells per volume / density per type','cells_per_volume'],['Total dendrite length per cell','length.dendrite'],['Total axon length per cell','length.axon'],
 ['Spherical range of dendrites (max reach per cell)','reach_max.dendrite'],['Spherical range of axons (max reach per cell)','reach_max.axon'],['Mean distance of dendrite from soma','reach_mean.dendrite'],['Mean distance of axon from soma','reach_mean.axon'],
 ['Target cells per cell (total, per target type)','targets'],['Source cells per cell (total, per source type)','sources'],['Connection probability','conn_prob'],['Synapses on axons (outgoing contacts per cell)','syn_axon'],
 ['Synapses on dendrites (incoming contacts per cell)','syn_dendrite'],['Contacts per connected pair','syn_per_pair'],['Heat map: centre / rim density (axon ball index)','ball_index']];
function lit(r){if(r.range){const[a,b]=r.range;return (a==null?'≥?':fmt(a))+' – '+(b==null?'∞':fmt(b))}if(r.value!=null)return fmt(r.value)+(r.sd!=null?' ± '+fmt(r.sd):'');return 'TODO'}
function checks(){
 const C=M.comparisons, cnt={};C.forEach(r=>cnt[r.status]=(cnt[r.status]||0)+1);
 let h=`<div class="card sum"><b>Profile ${esc(DATA.profile.name)}</b> <span class="mut">${esc(DATA.profile.description)}</span><div class="row">`+['pass','flag','unknown','info','n/a'].map(s=>`<span class="badge ${s=='n/a'?'na':s}">${s} ${cnt[s]||0}</span>`).join(' ')+`</div>
 <div class="small mut">pass = inside the literature range (or within ${M.defaults.sd_k} SD, or within ±${M.defaults.tolerance_rel*100}% of a single value); flag = outside; unknown = no literature number yet (TODO); info = not like-for-like (e.g. whole-cell axon vs a local patch); n/a = the model has no such metric. Every literature number in this profile is unverified (see the evidence column).</div></div>`;
 for(const[title,pre] of GROUPS){
  const keys=Object.keys(M.metrics).filter(k=>k===pre||k.startsWith(pre+'.')).filter(k=>!(pre==='targets'||pre==='sources'||pre==='syn_axon'||pre==='syn_dendrite')||true);
  if(!keys.length&&!C.some(r=>r.metric.startsWith(pre)))continue;
  h+=`<h2>${esc(title)}</h2>`;const cm=M.comments[pre];if(cm)h+=`<p class="mut small">${esc(cm)}</p>`;
  h+=`<div class="tw"><table><tr><th>metric</th><th>n</th><th>mean</th><th>median</th><th>min – max</th><th>literature</th><th>status</th><th>evidence / reference / tissue</th><th>comment</th></tr>`;
  for(const k of keys){const m=M.metrics[k], rows=C.filter(r=>r.metric===k);
   const base=`<td>${esc(k)}${m.note?'<div class="small mut">'+esc(m.note)+'</div>':''}</td><td class="n">${m.n??''}</td><td class="n">${fmt(m.mean)}</td><td class="n">${fmt(m.median)}</td><td class="n">${fmt(m.min)} – ${fmt(m.max)}</td>`;
   if(!rows.length){h+=`<tr>${base}<td class="mut">–</td><td><span class="badge unknown">unknown</span></td><td class="mut small">no entry in profile</td><td class="small">${esc(M.comments[k]||'')}</td></tr>`;continue}
   rows.forEach((r,i)=>{h+=`<tr>${i?'<td></td><td></td><td></td><td></td><td></td>':base}<td class="n">${lit(r)} <span class="mut">${esc(r.unit||'')}</span>${r.stat!=='mean'?' ('+esc(r.stat)+')':''}</td><td><span class="badge ${r.status=='n/a'?'na':r.status}">${r.status}</span>${r.derived_estimate?'<div class="small mut">derived estimate</div>':''}</td>
   <td class="small"><b>${r.verified?'verified':'unverified'}</b> · ${esc(r.evidence)}<br>${esc(r.reference)}<br><span class="mut">${esc(r.source_tissue)}</span></td><td class="small">${esc(r.comment||M.comments[k]||'')}</td></tr>`})}
  C.filter(r=>r.metric.startsWith(pre)&&!M.metrics[r.metric]).forEach(r=>{h+=`<tr><td>${esc(r.metric)}</td><td></td><td class="n">–</td><td class="n">–</td><td></td><td class="n">${lit(r)}</td><td><span class="badge ${r.status=='n/a'?'na':r.status}">${r.status}</span></td><td class="small">${esc(r.evidence)}<br>${esc(r.reference)}</td><td class="small">model has no such metric</td></tr>`});
  h+='</table></div>'}
 $('#t_checks').innerHTML=h}
function allm(){let h='<h2>All computed metrics</h2><p class="mut small">Type names are the profile\'s (model names mapped by the profile type_map: '+esc(JSON.stringify(M.type_map))+').</p><div class="tw"><table><tr><th>metric</th><th>n</th><th>mean</th><th>median</th><th>sd</th><th>min</th><th>p10</th><th>p90</th><th>max</th><th>note</th></tr>';
 for(const k of Object.keys(M.metrics).sort()){const m=M.metrics[k];h+=`<tr><td>${esc(k)}</td><td class="n">${m.n??''}</td>`+['mean','median','sd','min','p10','p90','max'].map(s=>`<td class="n">${fmt(m[s])}</td>`).join('')+`<td class="small mut">${esc(m.note||'')}</td></tr>`}
 $('#t_all').innerHTML=h+'</table></div>'}
function modelTab(){const mt=M.meta;let h=`<h2>Model</h2><div class="card"><table>`;
 const rows=[['name',M.name],['input format',mt.input_format],['path',mt.path],['cells',JSON.stringify(M.info.types)],['volume',fmt(M.info.volume_um3)+' um³ — '+M.info.volume_source],['region',JSON.stringify(M.region)],['neurite segments',M.info.n_segments],['synaptic contacts',M.info.n_contacts+' ('+(mt.contact_rule||'')+')'],['autapse contacts',M.info.n_autapse_contacts],['axon/dendrite labels',mt.axon_dendrite_labels],['radii',mt.radii],['cell types',mt.cell_type_source||'from input'],['grid',`${M.grid.shape.join(' × ')} voxels of ${M.grid.voxel_um} um, origin ${M.grid.origin_um.map(fmt).join(', ')}`],['length check (um)',JSON.stringify(M.grid.length_check_um)]];
 rows.forEach(([a,b])=>h+=`<tr><th>${esc(a)}</th><td>${esc(b)}</td></tr>`);h+='</table></div>';
 if(M.notes&&M.notes.length)h+='<h3>Notes</h3><ul>'+M.notes.map(n=>'<li>'+esc(n)+'</li>').join('')+'</ul>';
 h+='<h3>Raw metadata</h3><pre class="card">'+esc(JSON.stringify(Object.assign({},mt,{cell_labels:(mt.cell_labels||[]).length+' labels'}),null,1))+'</pre>';$('#t_model').innerHTML=h}
// ---------- heat map
const CM=[[68,1,84],[59,82,139],[33,145,140],[94,201,98],[253,231,37]];
function cmap(t){t=Math.max(0,Math.min(1,t));const x=t*4,i=Math.min(3,Math.floor(x)),f=x-i,a=CM[i],b=CM[i+1];return[a[0]+(b[0]-a[0])*f,a[1]+(b[1]-a[1])*f,a[2]+(b[2]-a[2])*f]}
function grid(key){const id=M.name+'|'+key;if(cache[id])return cache[id];const g=M.grids[key];const bin=atob(g.b64),n=bin.length,v=new Float32Array(n),L=Math.log(g.vmax/g.vmin||1);
 for(let i=0;i<n;i++){const q=bin.charCodeAt(i);v[i]=q?g.vmin*Math.exp((q-1)/254*L):0}return cache[id]={v,vmin:g.vmin,vmax:g.vmax,unit:g.unit}}
function heatUI(){const keys=Object.keys(M.grids);const S=M.grid.shape;
 let h=`<h2>3D density heat map</h2><p class="mut small">Neurite length density per ${M.grid.voxel_um} um voxel (km/mm³ = um of neurite per um³); soma and synapse grids in counts/mm³. Slices start at the region centre. Pick a grid, then move the slice sliders; "View" crops to the region (R = region radius). "Max projection" collapses the third axis. The 3D view shows voxels above the threshold; drag to rotate.</p>
 <div class="row"><label>Grid <select id="gsel">${keys.map(k=>`<option ${k==='axon_length.all'?'selected':''}>${k}</option>`).join('')}</select></label>
 <label>Scale <select id="gsc"><option value="log">log</option><option value="lin">linear</option></select></label><label>View <select id="gview"><option value="3">region ±3R</option><option value="1.5">region ±1.5R</option><option value="0">whole grid</option></select></label><label><input type="checkbox" id="gmip"> max projection</label><span id="gleg" class="small mut"></span></div>
 <div class="row"><label>z (XY) <input type="range" id="sz" min="0" max="${S[2]-1}"></label><label>y (XZ) <input type="range" id="sy" min="0" max="${S[1]-1}"></label><label>x (YZ) <input type="range" id="sx" min="0" max="${S[0]-1}"></label><span id="spos" class="small mut"></span></div>
 <div class="grid3"><div><div class="small">XY (top view)</div><canvas id="cxy"></canvas></div><div><div class="small">XZ (side view)</div><canvas id="cxz"></canvas></div><div><div class="small">YZ (side view)</div><canvas id="cyz"></canvas></div></div>
 <h3>3D view</h3><div class="row"><label>threshold (fraction of max, log scale) <input type="range" id="thr" min="0" max="100" value="35"></label><span class="small mut" id="npts"></span></div><canvas id="c3d" width="640" height="480" style="max-width:640px;cursor:grab"></canvas>`;
 $('#t_heat').innerHTML=h;const cu=M.radial.centre_um,C=(i)=>Math.max(0,Math.min(S[i]-1,Math.floor((cu[i]-M.grid.origin_um[i])/M.grid.voxel_um)));$('#sz').value=C(2);$('#sy').value=C(1);$('#sx').value=C(0);
 ['gsel','gsc','gmip','sz','sy','sx','gview'].forEach(i=>$('#'+i).oninput=drawHeat);$('#thr').oninput=draw3d;let drag=null;const c=$('#c3d');
 c.onmousedown=e=>drag=[e.clientX,e.clientY];window.onmouseup=()=>drag=null;c.onmousemove=e=>{if(!drag)return;rot[0]+=(e.clientX-drag[0])*0.01;rot[1]+=(e.clientY-drag[1])*0.01;drag=[e.clientX,e.clientY];draw3d()}}
let rot=[0.6,-0.9];
function val2t(v,g,lg){if(v<=0)return -1;return lg?Math.log(v/g.vmin)/Math.log(g.vmax/g.vmin):v/g.vmax}
function slice(cv,W,H,get,g,lg,sx,sy){cv.width=W;cv.height=H;const ctx=cv.getContext('2d'),im=ctx.createImageData(W,H);
 for(let j=0;j<H;j++)for(let i=0;i<W;i++){const v=get(i,H-1-j),t=val2t(v,g,lg),o=4*(j*W+i);if(t<0){im.data[o]=0;im.data[o+1]=0;im.data[o+2]=0}else{const c=cmap(t);im.data[o]=c[0];im.data[o+1]=c[1];im.data[o+2]=c[2]}im.data[o+3]=255}
 ctx.putImageData(im,0,0);cv.style.aspectRatio=W+'/'+H}
function crop(){const S=M.grid.shape,f=+$('#gview').value,o=M.grid.origin_um,vx=M.grid.voxel_um,c=M.radial.centre_um,R=M.radial.R_um;
 return [0,1,2].map(a=>{if(!f)return[0,S[a]];const lo=Math.max(0,Math.floor((c[a]-f*R-o[a])/vx)),hi=Math.min(S[a],Math.ceil((c[a]+f*R-o[a])/vx));return hi>lo?[lo,hi]:[0,S[a]]})}
function drawHeat(){if(!$('#gsel'))heatUI();const key=$('#gsel').value,g=grid(key),S=M.grid.shape,[nx,ny,nz]=S,lg=$('#gsc').value==='log',mip=$('#gmip').checked,v=g.v;
 const ix=(x,y,z)=>x+nx*(y+ny*z),z0=+$('#sz').value,y0=+$('#sy').value,x0=+$('#sx').value,o=M.grid.origin_um,vx=M.grid.voxel_um;
 const mx=(f,a,b)=>{let m=0;for(let k=a;k<b;k++){const q=f(k);if(q>m)m=q}return m};const [[xa,xb],[ya,yb],[za,zb]]=crop();
 slice($('#cxy'),xb-xa,yb-ya,(i,j)=>mip?mx(k=>v[ix(xa+i,ya+j,k)],za,zb):v[ix(xa+i,ya+j,z0)],g,lg);slice($('#cxz'),xb-xa,zb-za,(i,j)=>mip?mx(k=>v[ix(xa+i,k,za+j)],ya,yb):v[ix(xa+i,y0,za+j)],g,lg);slice($('#cyz'),yb-ya,zb-za,(i,j)=>mip?mx(k=>v[ix(k,ya+i,za+j)],xa,xb):v[ix(x0,ya+i,za+j)],g,lg);
 $('#spos').textContent=`x ${fmt(o[0]+(x0+.5)*vx)}  y ${fmt(o[1]+(y0+.5)*vx)}  z ${fmt(o[2]+(z0+.5)*vx)} um`;$('#gleg').textContent=`range ${fmt(g.vmin)} – ${fmt(g.vmax)} ${g.unit} (${lg?'log':'linear'} colour scale; black = 0)`;draw3d()}
function draw3d(){const c=$('#c3d');if(!c)return;const key=$('#gsel').value,g=grid(key),[nx,ny,nz]=M.grid.shape,v=g.v,thr=+$('#thr').value/100,ctx=c.getContext('2d');
 ctx.fillStyle='#000';ctx.fillRect(0,0,c.width,c.height);const pts=[];const [[xa,xb],[ya,yb],[za,zb]]=crop(),cx=(xa+xb)/2,cy=(ya+yb)/2,cz=(za+zb)/2,sc=Math.min(c.width,c.height)/Math.max(xb-xa,yb-ya,zb-za)*0.9;
 const ca=Math.cos(rot[0]),sa=Math.sin(rot[0]),cb=Math.cos(rot[1]),sb=Math.sin(rot[1]);
 for(let z=za;z<zb;z++)for(let y=ya;y<yb;y++)for(let x=xa;x<xb;x++){const t=val2t(v[x+nx*(y+ny*z)],g,true);if(t<thr)continue;let X=x-cx,Y=y-cy,Z=z-cz;const x1=ca*X-sa*Y,y1=sa*X+ca*Y;const y2=cb*y1-sb*Z,z2=sb*y1+cb*Z;pts.push([x1,z2,y2,t])}
 pts.sort((a,b)=>a[2]-b[2]);const r=Math.max(1.5,sc*0.7);for(const p of pts){const c3=cmap((p[3]-thr)/(1-thr||1));ctx.fillStyle=`rgba(${c3[0]|0},${c3[1]|0},${c3[2]|0},0.55)`;ctx.fillRect(c.width/2+p[0]*sc-r/2,c.height/2-p[1]*sc-r/2,r,r)}
 $('#npts').textContent=pts.length+' voxels shown'}
// ---------- radial
function radialUI(){const P=M.radial,keys=Object.keys(P.series);
 let h=`<h2>Radial profile</h2><p class="mut small">Neurite length density against the cylindrical distance r from the centre (${esc(P.centre_source)}; centre ${P.centre_um.map(fmt).join(', ')} um, R = ${fmt(P.R_um)} um). "Slab" counts only neurite within ±${fmt(P.slab_half_thickness_um)} um of the centre plane (km/mm³); "column" integrates over all z (um per um² of annulus). A peak at small r that falls towards the rim is the axon ball. Dashed lines: R/3, 2R/3, R.</p>
 <div class="row"><label>Mode <select id="rmode"><option value="slab_km_per_mm3">slab (km/mm³)</option><option value="column_um_per_um2">column (um/um²)</option></select></label><label><input type="checkbox" id="rlog"> log y</label></div>
 <div class="row small">${keys.map((k,i)=>`<label><input type="checkbox" class="rk" value="${k}" ${k.endsWith('.all')?'':'checked'}> ${k}</label>`).join(' ')}</div>
 <canvas id="rad" width="900" height="420" style="background:var(--card)"></canvas>
 <h3>Ball index (centre density / rim density, slab)</h3><table style="max-width:600px"><tr><th>series</th><th>ball index</th></tr>${keys.map(k=>`<tr><td>${k}</td><td class="n">${fmt(P.ball_index[k])}</td></tr>`).join('')}</table>`;
 $('#t_radial').innerHTML=h;['rmode','rlog'].forEach(i=>$('#'+i).oninput=drawRadial);document.querySelectorAll('.rk').forEach(e=>e.oninput=drawRadial)}
const PAL=['#2f6fb0','#d1603d','#3a9a5b','#8a5fc0','#b58b00','#c23b7a','#4aa3b5','#777'];
function drawRadial(){if(!$('#rad'))radialUI();const P=M.radial,c=$('#rad'),ctx=c.getContext('2d'),mode=$('#rmode').value,lg=$('#rlog').checked,E=P.r_edges_um,mid=E.slice(0,-1).map((e,i)=>(e+E[i+1])/2);
 const sel=[...document.querySelectorAll('.rk')].filter(e=>e.checked).map(e=>e.value);const W=c.width,H=c.height,l=70,r=20,t=20,b=45;
 const st=getComputedStyle(document.documentElement),fg=st.getPropertyValue('--fg'),mut=st.getPropertyValue('--mut'),line=st.getPropertyValue('--line');ctx.clearRect(0,0,W,H);
 let ymax=0,ymin=Infinity;sel.forEach(k=>P.series[k][mode].forEach(v=>{if(v>ymax)ymax=v;if(v>0&&v<ymin)ymin=v}));if(!ymax){ymax=1;ymin=1e-3}if(!lg)ymin=0;else ymin=Math.max(ymin,ymax*1e-4);
 const X=x=>l+(x/E[E.length-1])*(W-l-r),Y=y=>lg?(H-b)-(Math.log(Math.max(y,ymin)/ymin)/Math.log(ymax/ymin))*(H-b-t):(H-b)-(y/ymax)*(H-b-t);
 ctx.strokeStyle=line;ctx.fillStyle=mut;ctx.font='12px system-ui';ctx.beginPath();ctx.moveTo(l,t);ctx.lineTo(l,H-b);ctx.lineTo(W-r,H-b);ctx.stroke();
 for(let i=0;i<=5;i++){const xv=E[E.length-1]*i/5;ctx.fillText(fmt(xv),X(xv)-10,H-b+16)}ctx.fillText('r (um)',W/2,H-8);
 for(let i=0;i<=4;i++){const yv=lg?ymin*Math.pow(ymax/ymin,i/4):ymax*i/4;ctx.fillText(fmt(yv),4,Y(yv)+4)}
 ctx.setLineDash([4,4]);[P.R_um/3,2*P.R_um/3,P.R_um].forEach(x=>{ctx.beginPath();ctx.moveTo(X(x),t);ctx.lineTo(X(x),H-b);ctx.stroke()});ctx.setLineDash([]);
 sel.forEach((k,i)=>{ctx.strokeStyle=PAL[i%PAL.length];ctx.lineWidth=2;ctx.beginPath();P.series[k][mode].forEach((v,j)=>{const x=X(mid[j]),y=Y(v);j?ctx.lineTo(x,y):ctx.moveTo(x,y)});ctx.stroke();ctx.fillStyle=PAL[i%PAL.length];ctx.fillText(k,W-r-170,t+14+14*i)});ctx.lineWidth=1}
function load(i){M=DATA.models[i];$('#hdr').textContent=`profile ${DATA.profile.name} · generated ${DATA.generated} · ${M.meta.input_format} · ${M.meta.path}`;
 ['t_heat','t_radial'].forEach(t=>$('#'+t).innerHTML='');checks();allm();modelTab();const vis=TABS.find(([k])=>!$('#t_'+k).hidden);show(vis?vis[0]:'checks')}
DATA.models.forEach((m,i)=>{const o=document.createElement('option');o.value=i;o.textContent=m.name;$('#msel').appendChild(o)});$('#msel').onchange=e=>load(+e.target.value);
const HP=new URLSearchParams(location.hash.slice(1));const m0=Math.min(+(HP.get('model')||0),DATA.models.length-1);$('#msel').value=m0;tabs();load(m0);if(HP.get('tab'))show(HP.get('tab'));
document.title='Realism tester: '+DATA.models.map(m=>m.name).join(', ');
</script></body></html>
"""

#!/usr/bin/env python3
"""Create static PDF and self-contained interactive circos plots for JRe65 BND candidates."""
import csv, gzip, json, math, re
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.path import Path as MplPath
from matplotlib.patches import Arc, PathPatch

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[1]
VCF=PROJECT/'annotation/vep/sv/JRe65_Neuroblastoma.sv.phased.vep.vcf.gz'
TSV=HERE/'JRe65_ranked_BND_candidates.tsv'
PDF=HERE/'JRe65_SV_candidate_circos.pdf'
HTML=HERE/'JRe65_interactive_SV_candidate_circos.html'
CHROMS=[f'chr{i}' for i in range(1,23)]+['chrX','chrY']
TARGETS=[('SBF2','IQCJ'),('DDX10','SKA3'),('CD38','BRD10'),('DLG2','B3GLCT'),
         ('CRYZ','HOMER2'),('ZNF665','A4GNT'),('MSH3','IL1RAPL1'),('CADM2','MGAM'),
         ('HOXB3','LDAH'),('SYN3','ACOT13')]
COLORS=['#6f42c1','#1f77b4','#ff7f0e','#2ca02c','#d62728','#8c564b','#17becf','#9467bd','#bcbd22','#e377c2']

def lengths():
 out={}
 with gzip.open(VCF,'rt') as f:
  for line in f:
   if line.startswith('##contig=<ID='):
    m=re.match(r'##contig=<ID=([^,>]+),length=(\d+)',line)
    if m and m.group(1) in CHROMS:out[m.group(1)]=int(m.group(2))
   elif line.startswith('#CHROM'):break
 return {c:out[c] for c in CHROMS}

def candidates():
 with TSV.open() as f: rows=list(csv.DictReader(f,delimiter='\t'))
 by_pair={frozenset((r['gene1'],r['gene2'])):r for r in rows}
 out=[]
 for color_index,pair in enumerate(TARGETS):
  r=dict(by_pair[frozenset(pair)]);r['rank']=int(r['rank']);r['name']='–'.join(pair);r['color']=COLORS[color_index]
  for k in ('pos1','pos2','junction_count','support','ref_depth'):r[k]=int(float(r[k]))
  for k in ('af','gq','qual','score'):r[k]=float(r[k])
  out.append(r)
 out.sort(key=lambda r:r['rank'])
 return out

def ranked_candidates():
 with TSV.open() as f: rows=list(csv.DictReader(f,delimiter='\t'))
 out=[]
 for row in rows:
  r=dict(row);r['rank']=int(r['rank']);r['name']=f"{r['gene1']}–{r['gene2']}";r['color']=COLORS[(r['rank']-1)%len(COLORS)]
  for k in ('pos1','pos2','junction_count','support','ref_depth'):r[k]=int(float(r[k]))
  for k in ('af','gq','qual','score'):r[k]=float(r[k])
  out.append(r)
 return out

def spans(lens):
 gap=.018;total=sum(lens.values());usable=2*math.pi-gap*len(lens);a=-math.pi/2;out={}
 for c,n in lens.items():w=usable*n/total;out[c]=(a,a+w);a+=w+gap
 return out
def angle(span,lens,chrom,pos):return span[chrom][0]+(span[chrom][1]-span[chrom][0])*pos/lens[chrom]

def static_plot(data,lens):
 fig,ax=plt.subplots(figsize=(8,8),subplot_kw={'aspect':'equal'});ax.axis('off');s=spans(lens);r=1.0
 palette=['#5875a4','#d78b3f','#59a14f','#b55d60','#8064a2','#4e9b9b']
 for i,c in enumerate(CHROMS):
  a,b=s[c];ax.add_patch(Arc((0,0),2*r,2*r,theta1=math.degrees(a),theta2=math.degrees(b),lw=10,color=palette[i%len(palette)]))
  m=(a+b)/2;ax.text(1.13*math.cos(m),1.13*math.sin(m),c[3:],ha='center',va='center',fontsize=7,weight='bold')
 for d in data:
  a=angle(s,lens,d['chrom1'],d['pos1']);b=angle(s,lens,d['chrom2'],d['pos2']);p1=(.96*math.cos(a),.96*math.sin(a));p2=(.96*math.cos(b),.96*math.sin(b))
  path=MplPath([p1,(0,0),p2],[MplPath.MOVETO,MplPath.CURVE3,MplPath.CURVE3])
  ax.add_patch(PathPatch(path,fill=False,color=d['color'],lw=max(2,7-.45*(d['rank']-1)),alpha=.78,capstyle='round'))
 handles=[Line2D([0],[0],color=d['color'],lw=4,label=f"{d['rank']}. {d['name']}  ({d['junction_count']}J; {d['support']} alt reads)") for d in data]
 ax.legend(handles=handles,loc='lower center',bbox_to_anchor=(.5,-.12),ncol=2,frameon=False,fontsize=7)
 ax.set_xlim(-1.32,1.32);ax.set_ylim(-1.36,1.32);ax.set_title('JRe65 Neuroblastoma: top SV/BND candidates',fontsize=15,weight='bold',pad=15)
 fig.savefig(PDF,bbox_inches='tight');plt.close(fig)

HTML_TEMPLATE=r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>JRe65 Neuroblastoma — SV candidates</title><style>
:root{font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;color:#172033}body{margin:0;background:#f5f7fa}.page{max-width:1280px;margin:auto;padding:24px}h1{font-size:25px;margin:0 0 6px}.subtitle{color:#596579;margin-bottom:18px}.layout{display:grid;grid-template-columns:minmax(620px,1fr) 350px;gap:18px;align-items:start}.card{background:#fff;border:1px solid #dce2ea;border-radius:12px;box-shadow:0 3px 12px #17203310}#plotCard{position:relative;padding:10px}svg{width:100%;height:auto;display:block}.side{padding:18px}.side h2{font-size:16px;margin:0 0 12px}.controls{display:grid;gap:6px}.control{display:grid;grid-template-columns:18px 12px 1fr auto;gap:7px;align-items:center;font-size:12px;padding:5px;border-radius:6px}.control:hover{background:#f3f5f8}.swatch{width:12px;height:12px;border-radius:3px}.support{color:#687386}button{border:1px solid #cbd3de;background:white;border-radius:6px;padding:6px 9px;cursor:pointer;margin:8px 5px 14px 0}.notes{font-size:12px;color:#626f82;line-height:1.5;border-top:1px solid #e4e8ee;padding-top:12px}#tooltip{position:absolute;display:none;pointer-events:none;max-width:410px;background:#111827f2;color:#fff;padding:10px 12px;border-radius:7px;font-size:12px;line-height:1.45;box-shadow:0 4px 18px #0004;z-index:5}.chr-label{font-size:11px;fill:#253046;text-anchor:middle;font-weight:600}.chr-arc{fill:none;stroke-width:18}.chord{fill:none;stroke-linecap:round;cursor:pointer;transition:opacity .15s,stroke-width .15s}.chord:hover,.chord.selected{opacity:1!important}table{border-collapse:collapse;width:100%;font-size:12px;background:white}th,td{text-align:left;padding:8px;border-bottom:1px solid #e2e6ec}th{background:#eef2f6;position:sticky;top:0}.table-card{overflow:auto;max-height:460px;margin-top:18px}.table-tools{position:sticky;left:0;display:flex;flex-wrap:wrap;align-items:end;gap:8px;padding:14px 16px;background:white;border-bottom:1px solid #e2e6ec}.table-search{display:grid;gap:4px;flex:1 1 420px}.table-search label{font-size:12px;font-weight:700}.table-search input{width:100%;min-height:38px;padding:7px 10px;border:1px solid #a9b4bf;border-radius:6px;font:inherit}.table-search input:focus{outline:3px solid #73b9e755;border-color:#135c91}.table-status{color:#687386;font-size:12px;font-weight:650;padding-bottom:8px}@media(max-width:900px){.layout{grid-template-columns:1fr}.page{padding:12px}}
</style></head><body><main class="page"><h1>JRe65 Neuroblastoma: top SV/BND candidates</h1><div class="subtitle">GRCh38 · complete PASS mate pairs · evidence-ranked DNA rearrangements</div><div class="layout"><section id="plotCard" class="card"><svg id="circos" viewBox="85 140 650 540"></svg><div id="tooltip"></div></section><aside class="side card"><h2>SV candidates</h2><div class="controls" id="controls"></div><button id="all">Show all</button><button id="none">Hide all</button><div class="notes">Hover over a chord for breakpoint and support details; click to retain highlighting. “Prior” means the same gene pair was selected in JR21, JR22, or JR24 and therefore needs germline/artifact review.<br><br><b>MYCN note:</b> chr2:7,793,566 ↔ chr2:15,948,664 matches the amplified-region boundaries, but is excluded from these chords because it is MaxScoringDepth;MinQUAL with missing GT/AD.</div></aside></div><section class="table-card card"><div class="table-tools"><div class="table-search"><label for="candidate-search">Search ranked BND candidates</label><input id="candidate-search" type="search" autocomplete="off" placeholder="Gene symbol, candidate pair, chromosome, coordinate, consequence…"></div><div id="table-status" class="table-status" aria-live="polite"></div></div><table><thead><tr><th>Rank</th><th>Candidate</th><th>Breakpoint 1</th><th>Breakpoint 2</th><th>Junctions</th><th>AD (ref,alt)</th><th>Alt AF</th><th>GT</th><th>GQ</th><th>QUAL</th><th>Prior?</th><th>Consequences</th></tr></thead><tbody id="rows"></tbody></table></section></main>
<script>const fusions=__DATA__,ranked=__RANKED__,lengths=__LENGTHS__;const NS="http://www.w3.org/2000/svg",svg=document.getElementById('circos'),tip=document.getElementById('tooltip'),card=document.getElementById('plotCard'),cx=410,cy=410,r=216,gap=.018,chrs=Object.keys(lengths),total=Object.values(lengths).reduce((a,b)=>a+b,0),usable=Math.PI*2-gap*chrs.length,spans={};let an=-Math.PI/2;const pal=['#5875a4','#d78b3f','#59a14f','#b55d60','#8064a2','#4e9b9b'];function el(n,a={}){const x=document.createElementNS(NS,n);for(const[k,v]of Object.entries(a))x.setAttribute(k,v);return x}function polar(a,rad=r){return[cx+rad*Math.cos(a),cy+rad*Math.sin(a)]}function arc(a,b){const p=polar(a),q=polar(b);return`M${p[0]},${p[1]} A${r},${r} 0 ${b-a>Math.PI?1:0} 1 ${q[0]},${q[1]}`}chrs.forEach((c,i)=>{const w=usable*lengths[c]/total;spans[c]=[an,an+w];svg.appendChild(el('path',{d:arc(an,an+w),stroke:pal[i%pal.length],class:'chr-arc'}));const p=polar(an+w/2,r+28),t=el('text',{x:p[0],y:p[1]+4,class:'chr-label'});t.textContent=c.replace('chr','');svg.appendChild(t);an+=w+gap});function la(c,p){const s=spans[c];return s[0]+(s[1]-s[0])*p/lengths[c]}function fmt(n){return Number(n).toLocaleString()}function bp(c,p){return`${c}:${fmt(p)}`}function show(e,d){tip.innerHTML=`<b>Rank ${d.rank}: ${d.name}</b><br>${bp(d.chrom1,d.pos1)} ↔ ${bp(d.chrom2,d.pos2)}<br>Junctions: ${d.junction_count}; AD: ${d.ref_depth},${d.support} (ref,alt); AF: ${(100*d.af).toFixed(1)}%<br>GT: ${d.gt}; GQ: ${d.gq}; QUAL: ${d.qual}<br>${d.consequence1}<br>${d.consequence2}<br>Previously selected: ${d.seen_in_JR21_JR22_JR24}`;tip.style.display='block';const box=card.getBoundingClientRect();let x=e.clientX-box.left+12,y=e.clientY-box.top+12;if(x+tip.offsetWidth>box.width)x-=tip.offsetWidth+24;if(y+tip.offsetHeight>box.height)y-=tip.offsetHeight+24;tip.style.left=Math.max(5,x)+'px';tip.style.top=Math.max(5,y)+'px'}fusions.forEach((d,i)=>{const a=la(d.chrom1,d.pos1),b=la(d.chrom2,d.pos2),p=polar(a,r-13),q=polar(b,r-13),path=el('path',{d:`M${p[0]},${p[1]} Q${cx},${cy} ${q[0]},${q[1]}`,stroke:d.color,'stroke-width':Math.max(4,14-(d.rank-1)),opacity:.7,class:'chord','data-index':i});svg.insertBefore(path,svg.firstChild);path.onmousemove=e=>show(e,d);path.onmouseleave=()=>tip.style.display='none';path.onclick=()=>path.classList.toggle('selected');const c=document.createElement('label');c.className='control';c.innerHTML=`<input type="checkbox" checked><span class="swatch" style="background:${d.color}"></span><span>${d.rank}. ${d.name}${d.seen_in_JR21_JR22_JR24==='yes'?' †':''}</span><span class="support">${d.support} reads</span>`;document.getElementById('controls').appendChild(c);c.querySelector('input').onchange=e=>path.style.display=e.target.checked?'':'none'});ranked.forEach(d=>{const tr=document.createElement('tr');tr.innerHTML=`<td>${d.rank}</td><td><span class="swatch" style="display:inline-block;background:${d.color};margin-right:5px"></span>${d.name}</td><td>${bp(d.chrom1,d.pos1)}</td><td>${bp(d.chrom2,d.pos2)}</td><td>${d.junction_count}</td><td>${d.ref_depth},${d.support}</td><td>${(100*d.af).toFixed(1)}%</td><td>${d.gt}</td><td>${d.gq}</td><td>${d.qual}</td><td>${d.seen_in_JR21_JR22_JR24}</td><td>${d.consequence1}<br>${d.consequence2}</td>`;document.getElementById('rows').appendChild(tr)});const candidateSearch=document.getElementById('candidate-search'),tableStatus=document.getElementById('table-status'),tableRows=[...document.querySelectorAll('#rows tr')];function filterTable(){const terms=candidateSearch.value.toLocaleLowerCase().trim().split(/\s+/).filter(Boolean);let shown=0;tableRows.forEach(tr=>{const match=terms.every(term=>tr.textContent.toLocaleLowerCase().includes(term));tr.hidden=!match;if(match)shown++});tableStatus.textContent=`${shown.toLocaleString()} of ${ranked.length.toLocaleString()} candidates`};candidateSearch.addEventListener('input',filterTable);filterTable();function set(v){document.querySelectorAll('.control input').forEach(x=>{x.checked=v;x.dispatchEvent(new Event('change'))})}document.getElementById('all').onclick=()=>set(true);document.getElementById('none').onclick=()=>set(false);</script></body></html>'''

def interactive(data,ranked,lens):
 doc=HTML_TEMPLATE.replace('__DATA__',json.dumps(data,separators=(',',':'))).replace('__RANKED__',json.dumps(ranked,separators=(',',':'))).replace('__LENGTHS__',json.dumps(lens,separators=(',',':')))
 HTML.write_text(doc)

def main():
 data=candidates();ranked=ranked_candidates();lens=lengths();static_plot(data,lens);interactive(data,ranked,lens)
 print(f'Wrote {PDF}\nWrote {HTML}')
 for d in data:print(f"{d['rank']}. {d['name']}: {d['junction_count']} junction(s), {d['support']} alt reads")
if __name__=='__main__':main()

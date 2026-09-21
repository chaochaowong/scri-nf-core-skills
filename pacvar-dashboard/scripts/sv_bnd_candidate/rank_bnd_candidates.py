#!/usr/bin/env python3
"""Rank primary-chromosome, gene-linked Sawfish BND candidates from a VEP VCF."""
import csv, gzip, math, re
from collections import defaultdict
from pathlib import Path

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[1]
VCF=PROJECT/'annotation/vep/sv/JRe65_Neuroblastoma.sv.phased.vep.vcf.gz'
OUT=HERE/'JRe65_ranked_BND_candidates.tsv'
PRIMARY={f'chr{i}' for i in range(1,23)}|{'chrX','chrY'}
PRIOR_SELECTED={
 frozenset(x) for x in [
 ('EWSR1','FLI1'),('ADAMTS14','CD2AP'),('MYCT1','SGCD'),('SPRY3','TMLHE'),
 ('C1GALT1C1L','THADA'),('ADAMTS12','DEUP1'),('ADAMTS12','SRGAP2'),
 ('COG3','DNAJC25'),('IGLON5','NCOR2'),('ARHGAP19','FEZ1'),('IL1RAPL1','MSH3'),
 ('DEUP1','EYA1'),('CBX3','CCDC32'),('EPHA3','RARB'),('CADM2','MGAM'),
 ('DPP10','SET'),('CRYZ','HOMER2'),('COL6A6','PTPRR'),('EIF3H','STON2'),
 ('A4GNT','ZNF665'),('CT47A7','CT47B1'),('ARHGEF35','ENPP3'),
 ('CCDC146','RASA4'),('RHEX','UBTD1'),('FRMPD4','NBEA'),('ABCC2','GNPDA1'),
 ('IGSF10','MED12L'),('DNAJB4','FUBP1')]
}

def num(x):
 try:return float(x)
 except:return 0.0
def info_dict(s): return {x.partition('=')[0]:x.partition('=')[2] for x in s.split(';')}
def severity(c):
 weights={'transcript_ablation':9,'gene_fusion':9,'bidirectional_gene_fusion':9,'exon_loss_variant':8,
          'splice_acceptor_variant':8,'splice_donor_variant':8,'stop_gained':7,'frameshift_variant':7,
          'coding_sequence_variant':6,'transcript_amplification':5,'5_prime_UTR_variant':4,
          '3_prime_UTR_variant':4,'intron_variant':3,'non_coding_transcript_exon_variant':2,
          'upstream_gene_variant':1,'downstream_gene_variant':1}
 return max((weights.get(x,0) for x in c.split('&')),default=0)

def parse():
 records={}
 with gzip.open(VCF,'rt') as f:
  for line in f:
   if line.startswith('#'):continue
   a=line.rstrip().split('\t'); info=info_dict(a[7])
   if info.get('SVTYPE')!='BND':continue
   remote=re.search(r'[\[\]]([^:\[\]]+):(\d+)[\[\]]',a[4])
   if not remote:continue
   fmt=dict(zip(a[8].split(':'),a[9].split(':'))); ad=fmt.get('AD','0,0').split(',')
   anns=[]
   for csq in info.get('CSQ','').split(','):
    v=csq.split('|')
    if len(v)>=8 and v[3]:
     anns.append({'gene':v[3],'consequence':v[1],'impact':v[2],'transcript':v[6],
                  'biotype':v[7],'severity':severity(v[1])})
   # Keep the strongest annotation per local gene.
   genes={}
   for x in anns:
    key=(x['biotype']=='protein_coding',x['severity'])
    if x['gene'] not in genes or key>(genes[x['gene']]['biotype']=='protein_coding',genes[x['gene']]['severity']): genes[x['gene']]=x
   records[a[2]]={'id':a[2],'chrom':a[0],'pos':int(a[1]),'remote_chrom':remote.group(1),
    'remote_pos':int(remote.group(2)),'mateid':info.get('MATEID',''),'filter':a[6],'qual':num(a[5]),
    'gt':fmt.get('GT','.'),'gq':num(fmt.get('GQ')),'ref':int(num(ad[0])) if ad else 0,
    'alt_depth':sum(int(num(x)) for x in ad[1:]),'genes':genes,'alt':a[4]}
 return records

def main():
 HERE.mkdir(parents=True,exist_ok=True); records=parse(); events=[]; seen=set()
 for rid,left in records.items():
  if rid in seen:continue
  right=records.get(left['mateid']);seen.add(rid)
  if right:seen.add(right['id'])
  if not right or left['filter']!='PASS' or right['filter']!='PASS':continue
  if left['chrom'] not in PRIMARY or right['chrom'] not in PRIMARY:continue
  if not left['genes'] or not right['genes']:continue
  # Choose the most breakpoint-relevant coding gene at each endpoint.
  def best(gs): return sorted(gs.values(),key=lambda x:(x['biotype']=='protein_coding',x['severity']),reverse=True)[0]
  gl,gr=best(left['genes']),best(right['genes'])
  if gl['gene']==gr['gene']:continue
  endpoints=sorted([(left['chrom'],left['pos'],gl),(right['chrom'],right['pos'],gr)],key=lambda x:(x[0],x[1]))
  a,b=endpoints; support=min(left['alt_depth'],right['alt_depth']); ref=min(left['ref'],right['ref'])
  events.append({'gene1':a[2]['gene'],'gene2':b[2]['gene'],'chrom1':a[0],'pos1':a[1],
   'chrom2':b[0],'pos2':b[1],'consequence1':a[2]['consequence'],'consequence2':b[2]['consequence'],
   'biotype1':a[2]['biotype'],'biotype2':b[2]['biotype'],'support':support,'ref_depth':ref,
   'af':support/(support+ref) if support+ref else 0,'gq':min(left['gq'],right['gq']),
   'qual':min(left['qual'],right['qual']),'gt':left['gt'],'ids':left['id']+';'+right['id']})
 # Consolidate repeated nearby junction structures by unordered gene pair and chromosome pair.
 groups=defaultdict(list)
 for e in events:groups[(tuple(sorted((e['gene1'],e['gene2']))),tuple(sorted((e['chrom1'],e['chrom2']))))].append(e)
 rows=[]
 for (genes,chroms),es in groups.items():
  coding=sum(x.startswith('protein_coding') for e in es for x in (e['biotype1'],e['biotype2']))
  sev=max(severity(e['consequence1'])+severity(e['consequence2']) for e in es)
  maxsup=max(e['support'] for e in es); mingq=max(e['gq'] for e in es); minqual=max(e['qual'] for e in es)
  score=12*min(len(es),2)+4*math.log2(maxsup+1)+0.03*min(mingq,100)+0.003*min(minqual,999)+2*coding+sev+(3 if chroms[0]!=chroms[1] else 0)
  best_e=max(es,key=lambda e:(e['support'],e['gq'],e['qual']))
  rows.append({'score':score,'junction_count':len(es),**best_e,
   'seen_in_JR21_JR22_JR24':('yes' if frozenset((best_e['gene1'],best_e['gene2'])) in PRIOR_SELECTED else 'no'),
   'all_breakpoints':'; '.join(f"{e['chrom1']}:{e['pos1']}↔{e['chrom2']}:{e['pos2']}" for e in es),
   'all_ids':' | '.join(e['ids'] for e in es)})
 rows.sort(key=lambda x:(x['score'],x['support'],x['gq']),reverse=True)
 fields=['rank','score','gene1','gene2','chrom1','pos1','chrom2','pos2','junction_count','support','ref_depth','af','gq','qual','gt','consequence1','consequence2','biotype1','biotype2','seen_in_JR21_JR22_JR24','all_breakpoints','all_ids']
 with OUT.open('w',newline='') as f:
  w=csv.DictWriter(f,fields,delimiter='\t');w.writeheader()
  for i,row in enumerate(rows,1):row['rank']=i;row['score']=f"{row['score']:.2f}";row['af']=f"{row['af']:.3f}";w.writerow({k:row[k] for k in fields})
 print(f'complete gene-linked PASS events={len(events)}; grouped candidates={len(rows)}; wrote {OUT}')

if __name__=='__main__':main()

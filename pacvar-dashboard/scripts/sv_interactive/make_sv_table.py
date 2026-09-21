#!/usr/bin/env python3
"""Build a self-contained interactive table for non-BND structural variants."""

from __future__ import annotations

import gzip
import html
import json
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
INPUT = PROJECT / "annotation/vep/sv/JRe65_Neuroblastoma.sv.phased.vep.vcf.gz"
OUTPUT = HERE / "JRe65_Neuroblastoma.structural_variants.interactive.html"
SV_TYPES = {"INS", "DEL", "DUP", "INV"}
COLUMNS = ["CHROM", "POS", "END", "SIZE", "SVTYPE", "SVCLAIM", "ID", "FILTER",
           "QUAL", "GT", "CN", "GQ", "AD", "GENES", "CONSEQUENCES"]


def info_dict(value: str) -> dict[str, str]:
    result = {}
    for item in value.split(";"):
        key, sep, val = item.partition("=")
        result[key] = val if sep else "true"
    return result


def read_rows() -> list[list[str]]:
    rows = []
    with gzip.open(INPUT, "rt") as handle:
        for line in handle:
            if line.startswith("#"):
                continue
            fields = line.rstrip().split("\t")
            info = info_dict(fields[7])
            svtype = info.get("SVTYPE", "")
            if svtype not in SV_TYPES:
                continue
            fmt = dict(zip(fields[8].split(":"), fields[9].split(":")))
            end = int(info.get("END", fields[1]))
            svlen = info.get("SVLEN", "")
            size = abs(int(svlen.split(",")[0])) if svlen.lstrip("-").isdigit() else abs(end - int(fields[1]))
            genes, consequences = [], []
            for annotation in info.get("CSQ", "").split(","):
                values = annotation.split("|")
                if len(values) > 3 and values[3] and values[3] not in genes:
                    genes.append(values[3])
                if len(values) > 1:
                    for consequence in values[1].split("&"):
                        if consequence and consequence not in consequences:
                            consequences.append(consequence)
            rows.append([
                fields[0], fields[1], str(end), str(size), svtype, info.get("SVCLAIM", ""),
                fields[2], fields[6], fields[5], fmt.get("GT", ""), fmt.get("CN", ""),
                fmt.get("GQ", ""), fmt.get("AD", ""), ", ".join(genes),
                ", ".join(consequences),
            ])
    return rows


def main() -> None:
    rows = read_rows()
    counts = Counter(row[4] for row in rows)
    payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    OUTPUT.write_text(TEMPLATE.format(
        source=html.escape(INPUT.name), row_count=len(rows),
        counts=" &nbsp; · &nbsp; ".join(f"{name}: {counts[name]:,}" for name in ("INS", "DEL", "DUP", "INV")),
        columns=json.dumps(COLUMNS), rows=payload,
    ), encoding="utf-8")
    print(f"Wrote {OUTPUT} ({len(rows):,} records)")


TEMPLATE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>JRe65 structural variants</title>
<style>
:root {{--blue:#135c91;--pale:#eef6fb;--line:#cbd5df;--ink:#17212b;--muted:#607080}}
*{{box-sizing:border-box}} body{{margin:0;padding:24px;color:var(--ink);background:#f6f8fa;font:14px/1.4 system-ui,-apple-system,"Segoe UI",sans-serif}}
main{{max-width:1800px;margin:auto;background:white;padding:24px;border:1px solid #dde3e9;border-radius:10px;box-shadow:0 2px 8px #22334412}}
h1{{margin:0 0 4px;font-size:24px}} .subtitle{{margin:0 0 6px;color:#576574}} .counts{{margin:0 0 20px;color:#334e68;font-weight:700}}
.controls{{display:flex;flex-wrap:wrap;gap:14px;align-items:end;margin-bottom:14px}} .field{{display:grid;gap:5px}} .search{{flex:1 1 460px}}
label{{font-weight:650}} input,select{{min-height:38px;padding:7px 10px;border:1px solid #9eabb8;border-radius:5px;background:white;font:inherit}}
input:focus,select:focus{{outline:3px solid #73b9e755;border-color:var(--blue)}} .help{{color:var(--muted);font-size:12px}}
.status{{margin:8px 0;font-weight:650}} .table-wrap{{overflow:auto;max-height:68vh;border:1px solid var(--line)}}
table{{border-collapse:separate;border-spacing:0;min-width:100%;white-space:nowrap}} th,td{{padding:7px 9px;border-right:1px solid #e0e5ea;border-bottom:1px solid #e0e5ea;text-align:left;vertical-align:top;max-width:420px;overflow:hidden;text-overflow:ellipsis}}
th{{position:sticky;top:0;z-index:2;background:var(--blue);color:white;cursor:pointer;user-select:none}} th:hover{{background:#0d4b78}} th::after{{content:" ↕";opacity:.55}} th.asc::after{{content:" ▲";opacity:1}} th.desc::after{{content:" ▼";opacity:1}}
tbody tr:nth-child(even){{background:var(--pale)}} tbody tr:hover{{background:#fff4cf}} .type{{font-weight:800}} .INS{{color:#087f5b}} .DEL{{color:#1c6ca1}} .DUP{{color:#c92a2a}} .INV{{color:#7048a8}}
.pager{{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin-top:14px}} button{{min-width:38px;min-height:34px;padding:5px 10px;border:1px solid #a9b4bf;border-radius:5px;background:white;color:var(--ink);cursor:pointer}}
button:hover:not(:disabled){{border-color:var(--blue);color:var(--blue)}} button.active{{background:var(--blue);color:white;border-color:var(--blue)}} button:disabled{{opacity:.45;cursor:default}}
.empty{{padding:24px;text-align:center;color:#687683}} @media(max-width:700px){{body{{padding:8px}}main{{padding:14px}}}}
</style></head><body><main>
<h1>JRe65 Neuroblastoma — Structural variants</h1>
<p class="subtitle">Source: {source} · {row_count:,} non-BND records. Click any column heading to sort.</p>
<p class="counts">{counts}</p>
<div class="controls">
 <div class="field search"><label for="query">Search variants</label><input id="query" type="search" autocomplete="off" placeholder="Gene, chromosome, coordinate, ID, consequence…"><span class="help">Separate terms with spaces to require all terms.</span></div>
 <div class="field"><label for="typeFilter">SV type</label><select id="typeFilter"><option value="">All types</option><option>INS</option><option>DEL</option><option>DUP</option><option>INV</option></select></div>
 <div class="field"><label for="filterFilter">Call filter</label><select id="filterFilter"><option value="">All calls</option><option value="PASS">PASS only</option></select></div>
 <div class="field"><label for="pageSize">Rows per page</label><select id="pageSize"><option>25</option><option>50</option><option>100</option><option value="all">All</option></select></div>
</div>
<div id="status" class="status" aria-live="polite"></div><div class="table-wrap"><table><thead><tr id="head"></tr></thead><tbody id="body"></tbody></table></div><nav id="pager" class="pager" aria-label="Table pages"></nav>
</main><script id="columns-data" type="application/json">{columns}</script><script id="rows-data" type="application/json">{rows}</script>
<script>(()=>{{
const columns=JSON.parse(document.getElementById('columns-data').textContent),rows=JSON.parse(document.getElementById('rows-data').textContent);
const head=document.getElementById('head'),body=document.getElementById('body'),status=document.getElementById('status'),pager=document.getElementById('pager'),query=document.getElementById('query'),typeFilter=document.getElementById('typeFilter'),filterFilter=document.getElementById('filterFilter'),pageSize=document.getElementById('pageSize');
let filtered=rows.slice(),page=1,sortColumn=-1,sortDirection=1;
columns.forEach((name,i)=>{{const th=document.createElement('th');th.textContent=name;th.tabIndex=0;const sort=()=>{{if(sortColumn===i)sortDirection*=-1;else{{sortColumn=i;sortDirection=1}}page=1;render()}};th.onclick=sort;th.onkeydown=e=>{{if(e.key==='Enter'||e.key===' '){{e.preventDefault();sort()}}}};head.appendChild(th)}});
function compare(a,b){{const av=a[sortColumn]||'',bv=b[sortColumn]||'',an=Number(av),bn=Number(bv);if(av!==''&&bv!==''&&Number.isFinite(an)&&Number.isFinite(bn))return(an-bn)*sortDirection;return av.localeCompare(bv,undefined,{{numeric:true,sensitivity:'base'}})*sortDirection}}
function refilter(){{const terms=query.value.toLowerCase().trim().split(/\s+/).filter(Boolean),type=typeFilter.value,callFilter=filterFilter.value;filtered=rows.filter(r=>(!type||r[4]===type)&&(!callFilter||r[7]===callFilter)&&terms.every(t=>r.join(' ').toLowerCase().includes(t)));page=1;render()}}
function addButton(label,target,disabled=false,active=false){{const b=document.createElement('button');b.textContent=label;b.disabled=disabled;b.className=active?'active':'';b.onclick=()=>{{page=target;render()}};pager.appendChild(b)}}
function renderPager(total){{pager.replaceChildren();if(total<=1)return;addButton('Previous',page-1,page===1);const nums=[...new Set([1,total,page-2,page-1,page,page+1,page+2])].filter(n=>n>=1&&n<=total).sort((a,b)=>a-b);let last=0;nums.forEach(n=>{{if(last&&n-last>1){{const s=document.createElement('span');s.textContent='…';pager.appendChild(s)}}addButton(String(n),n,false,n===page);last=n}});addButton('Next',page+1,page===total)}}
function render(){{const ordered=sortColumn<0?filtered.slice():filtered.slice().sort(compare),size=pageSize.value==='all'?Math.max(ordered.length,1):Number(pageSize.value),pages=Math.max(1,Math.ceil(ordered.length/size));page=Math.min(page,pages);const first=(page-1)*size,slice=ordered.slice(first,first+size);body.replaceChildren();slice.forEach(row=>{{const tr=document.createElement('tr');row.forEach((v,i)=>{{const td=document.createElement('td');td.textContent=v;td.title=v;if(i===4)td.className=`type ${{v}}`;tr.appendChild(td)}});body.appendChild(tr)}});if(!slice.length){{const tr=document.createElement('tr'),td=document.createElement('td');td.colSpan=columns.length;td.className='empty';td.textContent='No matching variants';tr.appendChild(td);body.appendChild(tr)}}document.querySelectorAll('th').forEach((th,i)=>th.className=i===sortColumn?(sortDirection===1?'asc':'desc'):'');const last=Math.min(first+slice.length,ordered.length);status.textContent=ordered.length?`Showing ${{(first+1).toLocaleString()}}–${{last.toLocaleString()}} of ${{ordered.length.toLocaleString()}} matching records (${{rows.length.toLocaleString()}} total)`:`0 matching records (${{rows.length.toLocaleString()}} total)`;renderPager(pages)}}
query.oninput=refilter;typeFilter.onchange=refilter;filterFilter.onchange=refilter;pageSize.onchange=()=>{{page=1;render()}};render();
}})();</script></body></html>'''


if __name__ == "__main__":
    main()

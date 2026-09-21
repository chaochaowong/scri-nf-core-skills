#!/usr/bin/env python3
"""Build a self-contained tabbed chr1-22/X/Y CNV dosage HTML report."""

from __future__ import annotations

import gzip
import html
import json
import math
from collections import defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
VCF = PROJECT / "annotation/vep/sv/JRe65_Neuroblastoma.sv.phased.vep.vcf.gz"
CYTO = HERE / "cytoBandIdeo.hg38.txt.gz"
OUTPUT = HERE / "JRe65_genome_CNV_dosage_tabs.html"
CHROMS = [f"chr{i}" for i in range(1, 23)] + ["chrX", "chrY"]
COLORS = {"loss": "#2878b5", "gain": "#d73027"}
STAINS = {"gneg": "#fff", "gpos25": "#c8c8c8", "gpos50": "#969696",
          "gpos75": "#646464", "gpos100": "#111", "acen": "#df6666",
          "gvar": "#ddd", "stalk": "#b6d7e8"}


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def info_dict(text: str) -> dict[str, str]:
    return {piece.split("=", 1)[0]: piece.split("=", 1)[1]
            for piece in text.split(";") if "=" in piece}


def read_segments() -> tuple[dict[str, list[dict]], str]:
    result = defaultdict(list)
    sample = "sample"
    with gzip.open(VCF, "rt") as handle:
        for line in handle:
            if line.startswith("#CHROM"):
                sample = line.rstrip().split("\t")[9]
                continue
            if line.startswith("#"):
                continue
            row = line.rstrip().split("\t")
            if row[0] not in CHROMS:
                continue
            info = info_dict(row[7])
            if info.get("SVCLAIM") != "D" or info.get("SVTYPE") not in {"DEL", "DUP"}:
                continue
            fmt = dict(zip(row[8].split(":"), row[9].split(":")))
            if fmt.get("CN", ".") == ".":
                continue
            cn = float(fmt["CN"])
            log2_value = math.log2(cn / 2) if cn > 0 else None
            genes, consequences = [], []
            for annotation in info.get("CSQ", "").split(","):
                fields = annotation.split("|")
                if len(fields) > 3 and fields[3] and fields[3] not in genes:
                    genes.append(fields[3])
                if len(fields) > 1 and fields[1] and fields[1] not in consequences:
                    consequences.append(fields[1])
            result[row[0]].append({
                "chrom": row[0], "start": int(row[1]), "end": int(info["END"]),
                "id": row[2], "svtype": info["SVTYPE"], "svlen": info.get("SVLEN", "."),
                "cn": cn, "log2": log2_value, "qual": row[5], "filter": row[6],
                "gt": fmt.get("GT", "."), "cnq": fmt.get("CNQ", "."),
                "ad": fmt.get("AD", "."), "gq": fmt.get("GQ", "."),
                "pl": fmt.get("PL", "."), "ps": fmt.get("PS", "."),
                "pf": fmt.get("PF", "."), "format": row[8], "sample_values": row[9],
                "genes": ", ".join(genes) or ".",
                "consequences": ", ".join(consequences) or ".",
            })
    return result, sample


def read_bands() -> dict[str, list[dict]]:
    result = defaultdict(list)
    with gzip.open(CYTO, "rt") as handle:
        for line in handle:
            chrom, start, end, name, stain = line.rstrip().split("\t")
            if chrom in CHROMS:
                result[chrom].append({"start": int(start), "end": int(end), "name": name, "stain": stain})
    return result


def outline_path(bands, left, width, y0, height):
    right, ym, y1 = left + width, y0 + height / 2, y0 + height
    acen = [b for b in bands if b["stain"] == "acen"]
    if not acen:
        return f"M {left+9},{y0} H {right-9} Q {right},{y0} {right},{ym} Q {right},{y1} {right-9},{y1} H {left+9} Q {left},{y1} {left},{ym} Q {left},{y0} {left+9},{y0} Z"
    chrom_end = bands[-1]["end"]
    cs = left + acen[0]["start"] / chrom_end * width
    ce = left + acen[-1]["end"] / chrom_end * width
    cm = (cs + ce) / 2
    return (f"M {left+9},{y0} H {cs} C {cm-7},{y0} {cm-6},{ym-5} {cm},{ym-5} "
            f"C {cm+6},{ym-5} {cm+7},{y0} {ce},{y0} H {right-9} Q {right},{y0} {right},{ym} "
            f"Q {right},{y1} {right-9},{y1} H {ce} C {cm+7},{y1} {cm+6},{ym+5} {cm},{ym+5} "
            f"C {cm-6},{ym+5} {cm-7},{y1} {cs},{y1} H {left+9} Q {left},{y1} {left},{ym} "
            f"Q {left},{y0} {left+9},{y0} Z")


def chromosome_svg(chrom, bands, segments):
    width, height = 1160, 455
    left, right = 82, 24
    plot_width = width - left - right
    chrom_end = bands[-1]["end"]
    ide_y, ide_h = 42, 34
    path = outline_path(bands, left, plot_width, ide_y, ide_h)
    clip_id = f"clip-{chrom}"
    parts = [f'<svg viewBox="0 0 {width} {height}" class="chart" aria-label="{chrom} CNV dosage">',
             f'<defs><clipPath id="{clip_id}"><path d="{path}"/></clipPath></defs>',
             f'<text x="18" y="65" class="chrom-label">{chrom}</text>',
             f'<g clip-path="url(#{clip_id})">']
    for band in bands:
        x = left + band["start"] / chrom_end * plot_width
        w = (band["end"] - band["start"]) / chrom_end * plot_width
        tip = esc(f'{chrom}{band["name"]}: {band["start"]:,}–{band["end"]:,}')
        parts.append(f'<rect x="{x:.2f}" y="{ide_y}" width="{w:.2f}" height="{ide_h}" fill="{STAINS.get(band["stain"], "#eee")}" stroke="#666" stroke-width=".35"><title>{tip}</title></rect>')
    parts.extend(['</g>', f'<path d="{path}" fill="none" stroke="#222" stroke-width="1.4"/>'])

    top, bottom = 122, 395
    plot_h = bottom - top
    finite = [s["log2"] for s in segments if s["log2"] is not None]
    ymin = min([-3.5] if any(s["cn"] == 0 for s in segments) else [-1.25] + finite)
    ymax = max([1.4] + finite) + 0.25
    sy = lambda val: top + (ymax - val) / (ymax - ymin) * plot_h
    sx = lambda bp: left + bp / chrom_end * plot_width
    ticks = list(range(math.ceil(ymin), math.floor(ymax) + 1))
    for value in ticks:
        y = sy(value)
        parts.append(f'<line x1="{left}" x2="{width-right}" y1="{y:.2f}" y2="{y:.2f}" class="grid"/>')
        parts.append(f'<text x="{left-10}" y="{y+4:.2f}" text-anchor="end" class="tick">{value}</text>')
    yzero = sy(0)
    parts.append(f'<line x1="{left}" x2="{width-right}" y1="{yzero:.2f}" y2="{yzero:.2f}" class="baseline"/>')
    step = 25 if chrom_end > 120_000_000 else 10
    for mb in range(0, int(chrom_end / 1e6) + 1, step):
        x = sx(mb * 1e6)
        parts.append(f'<line x1="{x:.2f}" x2="{x:.2f}" y1="{bottom}" y2="{bottom+5}" class="axis"/><text x="{x:.2f}" y="{bottom+20}" text-anchor="middle" class="tick">{mb}</text>')
    for seg in segments:
        plotted = seg["log2"] if seg["log2"] is not None else -3.5
        x1, x2, y = sx(seg["start"]), sx(seg["end"]), sy(plotted)
        x2 = max(x2, x1 + 3)
        color = COLORS["gain" if seg["cn"] > 2 else "loss"]
        payload = esc(json.dumps(seg, separators=(",", ":")))
        parts.append(f'<line class="segment" x1="{x1:.2f}" x2="{x2:.2f}" y1="{y:.2f}" y2="{y:.2f}" stroke="{color}" data-record="{payload}"/>')
    if not segments:
        parts.append(f'<text x="{left+plot_width/2}" y="{top+plot_h/2}" text-anchor="middle" class="no-calls">No depth-based CNV calls on {chrom}</text>')
    parts.append(f'<text x="{left+plot_width/2}" y="445" text-anchor="middle" class="axis-label">GRCh38 position (Mb)</text>')
    parts.append(f'<text transform="translate(18,{top+plot_h/2}) rotate(-90)" text-anchor="middle" class="axis-label">log₂(CN/2)</text></svg>')
    return "".join(parts)


def main():
    segments, sample = read_segments()
    bands = read_bands()
    buttons, panels = [], []
    for index, chrom in enumerate(CHROMS):
        active = " active" if index == 0 else ""
        buttons.append(f'<button class="tab-button{active}" data-target="panel-{chrom}">{chrom.removeprefix("chr")}</button>')
        panels.append(f'<section id="panel-{chrom}" class="tab-panel{active}"><div class="call-count">{len(segments[chrom])} CNV segments</div>{chromosome_svg(chrom, bands[chrom], segments[chrom])}</section>')
    document = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>JRe65 genome CNV dosage</title>
<style>
body{{font-family:Arial,sans-serif;margin:20px;color:#222;background:#fafafa}} h1{{font-size:23px;margin:0 0 4px}}
.subtitle{{color:#555;margin:0 0 12px}} .tabs{{display:flex;flex-wrap:wrap;gap:5px;margin:12px 0}}
.tab-button{{border:1px solid #aaa;background:#eee;border-radius:5px;padding:6px 10px;cursor:pointer;font-weight:bold}}
.tab-button:hover{{background:#ddd}} .tab-button.active{{background:#333;color:white;border-color:#333}}
.tab-panel{{display:none;position:relative}} .tab-panel.active{{display:block}} .call-count{{position:absolute;right:18px;top:8px;color:#666;font-size:12px}}
.chart{{width:min(1160px,100%);height:auto;background:white;border:1px solid #ddd}} .chrom-label{{font-size:14px;font-weight:bold}}
.grid{{stroke:#e2e2e2}} .baseline{{stroke:#555;stroke-width:1.2;stroke-dasharray:5 4}} .axis{{stroke:#555}}
.tick{{font-size:11px;fill:#555}} .axis-label{{font-size:13px}} .segment{{stroke-width:7;cursor:pointer;transition:stroke-width .08s}}
.segment:hover{{stroke-width:12}} .segment.selected{{stroke:#ffbf00!important;stroke-width:14;filter:drop-shadow(0 0 3px #444)}}
.no-calls{{font-size:16px;fill:#888}} .legend{{font-size:13px;margin:8px 0}}
.sw{{display:inline-block;width:18px;height:6px;margin:0 5px 2px 14px}} #tip{{position:fixed;display:none;pointer-events:none;background:rgba(20,20,20,.96);color:white;padding:10px 12px;border-radius:5px;font-size:12px;line-height:1.45;max-width:min(540px,calc(100vw - 28px));max-height:calc(100vh - 28px);overflow-y:auto;overflow-wrap:anywhere;z-index:20;box-shadow:0 2px 9px #777}}
.search-box{{display:flex;flex-wrap:wrap;align-items:center;gap:7px;background:#fff;border:1px solid #ccc;border-radius:7px;padding:10px;margin:12px 0;max-width:820px}}
.search-box label{{font-weight:bold}} #gene-search{{padding:7px 9px;border:1px solid #999;border-radius:4px;font-size:14px;width:190px;text-transform:uppercase}}
.search-box button{{padding:7px 10px;border:1px solid #777;border-radius:4px;background:#eee;cursor:pointer}} .search-box button:hover{{background:#ddd}}
#search-status{{font-size:13px;color:#555}} #search-result{{display:none;background:#fff8dc;border-left:5px solid #ffbf00;padding:9px 12px;margin:8px 0 12px;max-width:980px;font-size:13px;line-height:1.45}}
.search-callout text{{font-size:11px;font-weight:bold;fill:#8b1a1a}} .search-callout rect{{fill:#fff8dc;stroke:#8b1a1a}} .search-callout line{{stroke:#8b1a1a;stroke-width:1.5}}
</style></head><body><h1>JRe65 Neuroblastoma — Genome copy-number dosage</h1>
<p class="subtitle">Sample: {esc(sample)}. Select a chromosome and hover over a segment for complete call details.</p>
<div class="legend"><span class="sw" style="background:{COLORS['loss']}"></span>Loss <span class="sw" style="background:{COLORS['gain']}"></span>Gain</div>
<div class="search-box"><label for="gene-search">Find VEP gene:</label><input id="gene-search" type="search" placeholder="e.g. MYCN" autocomplete="off"><button id="search-button">Search</button><button id="previous-match" hidden>Previous</button><button id="next-match" hidden>Next</button><span id="search-status"></span></div>
<div id="search-result"></div><nav class="tabs">{''.join(buttons)}</nav>{''.join(panels)}<div id="tip"></div>
<script>
const tip=document.getElementById('tip'); const missing=v=>(v===undefined||v===null||v===''||v==='.')?'not available':v;
function placeTip(e){{const gap=14,pad=8,w=tip.offsetWidth,h=tip.offsetHeight;let x=e.clientX+gap,y=e.clientY+gap;if(x+w>window.innerWidth-pad)x=e.clientX-w-gap;if(y+h>window.innerHeight-pad)y=e.clientY-h-gap;tip.style.left=Math.max(pad,Math.min(x,window.innerWidth-w-pad))+'px';tip.style.top=Math.max(pad,Math.min(y,window.innerHeight-h-pad))+'px';}}
function activateTab(chrom){{document.querySelectorAll('.tab-button,.tab-panel').forEach(x=>x.classList.remove('active'));const b=document.querySelector(`[data-target="panel-${{chrom}}"]`);b.classList.add('active');document.getElementById(b.dataset.target).classList.add('active');tip.style.display='none';}}
document.querySelectorAll('.tab-button').forEach(b=>b.onclick=()=>activateTab(b.dataset.target.replace('panel-','')));
document.querySelectorAll('.segment').forEach(el=>{{el.addEventListener('mousemove',e=>{{const d=JSON.parse(el.dataset.record);const l=d.log2===null?'−∞ (CN=0; drawn at −3.5)':d.log2.toFixed(3);tip.innerHTML=`<b>${{d.svtype}} ${{d.chrom}}:${{d.start.toLocaleString()}}–${{d.end.toLocaleString()}}</b><br>CN: <b>${{d.cn}}</b> &nbsp; log₂(CN/2): ${{l}}<br>GT: ${{missing(d.gt)}} &nbsp; CNQ: ${{missing(d.cnq)}} &nbsp; AD: ${{missing(d.ad)}} &nbsp; GQ: ${{missing(d.gq)}}<br>PL: ${{missing(d.pl)}} &nbsp; PS: ${{missing(d.ps)}} &nbsp; PF: ${{missing(d.pf)}}<br>QUAL: ${{d.qual}} &nbsp; FILTER: ${{d.filter}}<br>ID: ${{d.id}}<br>VEP genes: ${{d.genes}}<br>Consequences: ${{d.consequences}}<br>FORMAT: ${{d.format}}<br>Sample values: ${{d.sample_values}}`;tip.style.display='block';placeTip(e);}});el.addEventListener('mouseleave',()=>tip.style.display='none');}});
let matches=[], matchIndex=0, searchGene='';
const status=document.getElementById('search-status'), result=document.getElementById('search-result'), prev=document.getElementById('previous-match'), next=document.getElementById('next-match');
function showMatch(index){{
 matchIndex=(index+matches.length)%matches.length; const el=matches[matchIndex], d=JSON.parse(el.dataset.record); activateTab(d.chrom);
 document.querySelectorAll('.segment.selected').forEach(x=>x.classList.remove('selected')); document.querySelectorAll('.search-callout').forEach(x=>x.remove()); el.classList.add('selected');
 const svg=el.ownerSVGElement, ns='http://www.w3.org/2000/svg', x=(+el.getAttribute('x1') + +el.getAttribute('x2'))/2, y=+el.getAttribute('y1');
 const labelX=Math.max(105,Math.min(930,x-95)), labelY=Math.max(91,y-48), g=document.createElementNS(ns,'g'); g.setAttribute('class','search-callout');
 g.innerHTML=`<line x1="${{labelX+95}}" y1="${{labelY+34}}" x2="${{x}}" y2="${{y}}"/><rect x="${{labelX}}" y="${{labelY}}" width="190" height="34" rx="4"/><text x="${{labelX+7}}" y="${{labelY+14}}">${{searchGene}} — ${{d.svtype}}, CN=${{d.cn}}</text><text x="${{labelX+7}}" y="${{labelY+28}}">${{d.chrom}}:${{d.start.toLocaleString()}}–${{d.end.toLocaleString()}}</text>`; svg.appendChild(g);
 status.textContent=`Match ${{matchIndex+1}} of ${{matches.length}}`; const l=d.log2===null?'−∞':d.log2.toFixed(3); result.style.display='block';
 result.innerHTML=`<b>${{searchGene}} match:</b> ${{d.svtype}} <b>${{d.chrom}}:${{d.start.toLocaleString()}}–${{d.end.toLocaleString()}}</b> &nbsp; CN=${{d.cn}}; log₂(CN/2)=${{l}}; GT=${{missing(d.gt)}}; CNQ=${{missing(d.cnq)}}; FILTER=${{d.filter}}<br><b>VEP genes:</b> ${{d.genes}}<br><b>Consequences:</b> ${{d.consequences}}`;
}}
function search(){{
 searchGene=document.getElementById('gene-search').value.trim().toUpperCase(); document.querySelectorAll('.segment.selected').forEach(x=>x.classList.remove('selected'));document.querySelectorAll('.search-callout').forEach(x=>x.remove());result.style.display='none';
 if(!searchGene){{matches=[];status.textContent='Enter a gene symbol.';prev.hidden=next.hidden=true;return;}}
 const records=[...document.querySelectorAll('.segment')]; const exact=records.filter(el=>JSON.parse(el.dataset.record).genes.split(',').map(x=>x.trim().toUpperCase()).includes(searchGene));
 matches=exact.length?exact:records.filter(el=>JSON.parse(el.dataset.record).genes.toUpperCase().includes(searchGene));
 if(!matches.length){{status.textContent=`No VEP gene matches for “${{searchGene}}”.`;prev.hidden=next.hidden=true;return;}}
 prev.hidden=next.hidden=matches.length<2; showMatch(0);
}}
document.getElementById('search-button').onclick=search;document.getElementById('gene-search').addEventListener('keydown',e=>{{if(e.key==='Enter')search();}});prev.onclick=()=>showMatch(matchIndex-1);next.onclick=()=>showMatch(matchIndex+1);
</script><p class="subtitle">Note: CN=0 has undefined log₂(CN/2) and is displayed at −3.5. X/Y are also normalized to diploid CN=2 for consistency.</p></body></html>'''
    OUTPUT.write_text(document)
    print(f"Wrote {OUTPUT}")
    print("CNV calls:", sum(len(segments[c]) for c in CHROMS))


if __name__ == "__main__":
    main()

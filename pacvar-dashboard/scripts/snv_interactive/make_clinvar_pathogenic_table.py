#!/usr/bin/env python3
"""Build a self-contained interactive HTML table from the ClinVar CSV."""

import argparse
import csv
import html
import json
from pathlib import Path


DEFAULT_INPUT = Path(
    "annotation/vep/snv/"
    "JRe65_Neuroblastoma.snv.phased.vep.clinvar_pathogenic.csv"
)
DEFAULT_OUTPUT = Path(
    "downstream/snv_interactive/"
    "JRe65_Neuroblastoma.clinvar_pathogenic.interactive.html"
)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main():
    args = parse_args()
    build_table(
        args.input,
        args.output,
        title="JRe65 ClinVar pathogenic variants",
        search_names=['SYMBOL', 'HGVSg', 'HGVSc', 'HGVSp', 'ID', 'Existing_variation'],
    )


def build_table(input_path, output_path, title, search_names, selected_columns=None):
    with input_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        source_columns = reader.fieldnames or []
        columns = selected_columns or source_columns
        missing = [column for column in columns if column not in source_columns]
        if missing:
            raise ValueError(f"Missing input columns: {', '.join(missing)}")
        rows = [[row.get(column, "") for column in columns] for row in reader]

    # Prevent an embedded value from prematurely ending the JSON script element.
    data_json = json.dumps(rows, ensure_ascii=False).replace("</", "<\\/")
    columns_json = json.dumps(columns, ensure_ascii=False).replace("</", "<\\/")
    source_name = html.escape(input_path.name)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(TEMPLATE.format(
        title=html.escape(title),
        source_name=source_name,
        row_count=len(rows),
        columns_json=columns_json,
        data_json=data_json,
        search_names_json=json.dumps(search_names, ensure_ascii=False),
        search_help=html.escape(", ".join(search_names)),
    ), encoding="utf-8")
    print(f"Wrote {output_path} ({len(rows)} rows, {len(columns)} columns)")


TEMPLATE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
:root {{ --blue:#135c91; --pale:#eef6fb; --line:#cbd5df; --ink:#17212b; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; padding:24px; color:var(--ink); background:#f6f8fa;
       font:14px/1.4 system-ui,-apple-system,"Segoe UI",sans-serif; }}
main {{ max-width:1800px; margin:auto; background:white; padding:24px;
       border:1px solid #dde3e9; border-radius:10px; box-shadow:0 2px 8px #22334412; }}
h1 {{ margin:0 0 4px; font-size:24px; }}
.subtitle {{ margin:0 0 20px; color:#576574; }}
.controls {{ display:flex; flex-wrap:wrap; gap:14px; align-items:end; margin-bottom:14px; }}
.field {{ display:grid; gap:5px; }}
.field.search {{ flex:1 1 480px; }}
label {{ font-weight:650; }}
input,select {{ min-height:38px; padding:7px 10px; border:1px solid #9eabb8;
               border-radius:5px; background:white; font:inherit; }}
input:focus,select:focus {{ outline:3px solid #73b9e755; border-color:var(--blue); }}
.help {{ color:#667482; font-size:12px; }}
.status {{ margin:8px 0; font-weight:600; }}
.table-wrap {{ overflow:auto; max-height:68vh; border:1px solid var(--line); }}
table {{ border-collapse:separate; border-spacing:0; min-width:100%; white-space:nowrap; }}
th,td {{ padding:7px 9px; border-right:1px solid #e0e5ea; border-bottom:1px solid #e0e5ea;
         text-align:left; vertical-align:top; max-width:520px; overflow:hidden; text-overflow:ellipsis; }}
th {{ position:sticky; top:0; z-index:2; background:var(--blue); color:white;
      cursor:pointer; user-select:none; }}
th:hover {{ background:#0d4b78; }}
th::after {{ content:" ↕"; opacity:.55; }}
th.asc::after {{ content:" ▲"; opacity:1; }}
th.desc::after {{ content:" ▼"; opacity:1; }}
tbody tr:nth-child(even) {{ background:var(--pale); }}
tbody tr:hover {{ background:#fff4cf; }}
.pager {{ display:flex; flex-wrap:wrap; align-items:center; gap:6px; margin-top:14px; }}
button {{ min-width:38px; min-height:34px; padding:5px 10px; border:1px solid #a9b4bf;
         border-radius:5px; background:white; color:var(--ink); cursor:pointer; }}
button:hover:not(:disabled) {{ border-color:var(--blue); color:var(--blue); }}
button.active {{ background:var(--blue); color:white; border-color:var(--blue); }}
button:disabled {{ opacity:.45; cursor:default; }}
.empty {{ padding:24px; text-align:center; color:#687683; }}
@media (max-width:700px) {{ body {{ padding:8px; }} main {{ padding:14px; }} }}
</style>
</head>
<body>
<main>
  <h1>{title}</h1>
  <p class="subtitle">Source: {source_name} · {row_count} annotation rows. Click any column heading to sort.</p>
  <div class="controls">
    <div class="field search">
      <label for="query">Search gene or variant</label>
      <input id="query" type="search" autocomplete="off"
             placeholder="e.g. TP53, chr17:g.7673803C&gt;T, c.743G&gt;A, p.Arg248Gln, rs…">
      <span class="help">Searches {search_help}. Plain text allows partial matches; quote one gene symbol (for example, &quot;WT1&quot;) for an exact SYMBOL match.</span>
    </div>
    <div class="field">
      <label for="pageSize">Rows per page</label>
      <select id="pageSize"><option>25</option><option>50</option><option>100</option><option value="all">All</option></select>
    </div>
  </div>
  <div id="status" class="status" aria-live="polite"></div>
  <div class="table-wrap">
    <table id="variants"><thead><tr id="head"></tr></thead><tbody id="body"></tbody></table>
  </div>
  <nav id="pager" class="pager" aria-label="Table pages"></nav>
</main>
<script id="columns-data" type="application/json">{columns_json}</script>
<script id="rows-data" type="application/json">{data_json}</script>
<script>
(() => {{
  const columns = JSON.parse(document.getElementById('columns-data').textContent);
  const rows = JSON.parse(document.getElementById('rows-data').textContent);
  const searchNames = {search_names_json};
  const searchIndexes = searchNames.map(n => columns.indexOf(n)).filter(i => i >= 0);
  const query = document.getElementById('query');
  const symbolIndex = columns.indexOf('SYMBOL');
  const pageSize = document.getElementById('pageSize');
  const head = document.getElementById('head');
  const body = document.getElementById('body');
  const status = document.getElementById('status');
  const pager = document.getElementById('pager');
  let filtered = rows.slice(), page = 1, sortColumn = -1, sortDirection = 1;

  columns.forEach((name, i) => {{
    const th = document.createElement('th');
    th.textContent = name;
    th.title = `Sort by ${{name}}`;
    th.tabIndex = 0;
    const sort = () => {{
      if (sortColumn === i) sortDirection *= -1;
      else {{ sortColumn = i; sortDirection = 1; }}
      page = 1; render();
    }};
    th.addEventListener('click', sort);
    th.addEventListener('keydown', e => {{ if (e.key === 'Enter' || e.key === ' ') {{ e.preventDefault(); sort(); }} }});
    head.appendChild(th);
  }});

  function compare(a, b) {{
    const av = a[sortColumn] || '', bv = b[sortColumn] || '';
    const an = Number(av), bn = Number(bv);
    if (av !== '' && bv !== '' && Number.isFinite(an) && Number.isFinite(bn)) return (an - bn) * sortDirection;
    return av.localeCompare(bv, undefined, {{numeric:true, sensitivity:'base'}}) * sortDirection;
  }}

  function refilter() {{
    const rawQuery = query.value.toLocaleLowerCase().trim();
    const terms = rawQuery.split(/\s+/).filter(Boolean);
    const exactGeneMatch = rawQuery.match(/^"([^"]+)"$/);
    filtered = exactGeneMatch && symbolIndex >= 0
      ? rows.filter(row => (row[symbolIndex] || '').toLocaleLowerCase().trim() === exactGeneMatch[1].trim())
      : terms.length ? rows.filter(row => {{
      const haystack = searchIndexes.map(i => row[i] || '').join(' ').toLocaleLowerCase();
      return terms.every(term => haystack.includes(term));
    }}) : rows.slice();
    page = 1; render();
  }}

  function addButton(text, target, disabled=false, active=false) {{
    const button = document.createElement('button');
    button.type = 'button'; button.textContent = text; button.disabled = disabled;
    if (active) {{ button.className = 'active'; button.setAttribute('aria-current','page'); }}
    button.addEventListener('click', () => {{ page = target; render(); }});
    pager.appendChild(button);
  }}

  function renderPager(totalPages) {{
    pager.replaceChildren();
    if (totalPages <= 1) return;
    addButton('Previous', page - 1, page === 1);
    let candidates = new Set([1, totalPages, page-2, page-1, page, page+1, page+2]);
    let pages = [...candidates].filter(n => n >= 1 && n <= totalPages).sort((a,b) => a-b);
    let prior = 0;
    pages.forEach(n => {{
      if (prior && n - prior > 1) {{ const span=document.createElement('span'); span.textContent='…'; pager.appendChild(span); }}
      addButton(String(n), n, false, n === page); prior = n;
    }});
    addButton('Next', page + 1, page === totalPages);
  }}

  function render() {{
    head.querySelectorAll('th').forEach((th,i) => th.className = i === sortColumn ? (sortDirection === 1 ? 'asc' : 'desc') : '');
    const ordered = sortColumn >= 0 ? filtered.slice().sort(compare) : filtered;
    const size = pageSize.value === 'all' ? Math.max(ordered.length,1) : Number(pageSize.value);
    const totalPages = Math.max(1, Math.ceil(ordered.length / size));
    page = Math.min(page, totalPages);
    const start = (page - 1) * size;
    const visible = ordered.slice(start, start + size);
    body.replaceChildren();
    if (!visible.length) {{
      const tr=document.createElement('tr'), td=document.createElement('td');
      td.colSpan=columns.length; td.className='empty'; td.textContent='No matching variants';
      tr.appendChild(td); body.appendChild(tr);
    }} else visible.forEach(row => {{
      const tr=document.createElement('tr');
      row.forEach(value => {{ const td=document.createElement('td'); td.textContent=value; td.title=value; tr.appendChild(td); }});
      body.appendChild(tr);
    }});
    const first = ordered.length ? start + 1 : 0, last = Math.min(start + size, ordered.length);
    status.textContent = `Showing ${{first.toLocaleString()}}–${{last.toLocaleString()}} of ${{ordered.length.toLocaleString()}} matching rows (${{rows.length.toLocaleString()}} total)`;
    renderPager(totalPages);
  }}

  let timer;
  query.addEventListener('input', () => {{ clearTimeout(timer); timer=setTimeout(refilter,120); }});
  pageSize.addEventListener('change', () => {{ page=1; render(); }});
  render();
}})();
</script>
</body>
</html>
'''


if __name__ == "__main__":
    main()

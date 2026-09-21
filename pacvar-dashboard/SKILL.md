---
name: pacvar-dashboard
description: Build per-sample interactive HTML dashboards from VEP-annotated nf-core/pacvar SNV, structural-variant, breakend/fusion-candidate, and copy-number outputs. Use when a user wants to inspect a completed pacvar project and generate or refresh its variant reports and integrated sample index pages.
---

# Build a pacvar variant dashboard

Create portable, self-contained HTML reports inside a completed pacvar project. Treat pipeline results as read-only inputs. Copy and adapt the example generators from this skill's `scripts/` directory; never modify the examples in place while producing a project dashboard.

## Get the project directory

Ask the user for the pacvar project directory before doing any work. Resolve it to a canonical absolute path with `realpath -e -- <project-directory>`. If it does not exist or is not a directory, stop and ask for a valid path. If the resolved path differs from the supplied path, tell the user which physical path will be used.

The project may contain one or more samples. Discover sample IDs from the input filenames and, for VCF files, confirm them from the `#CHROM` sample columns. Do not infer a sample ID solely from the project-directory name. If filenames and VCF headers disagree or a file cannot be assigned unambiguously, show the conflicting values and ask the user to identify the intended sample mapping before generating reports.

## Preflight the annotated inputs

Require `<project-directory>/annotation/vep`. If it is absent, stop the workflow and explain that the dashboard requires VEP-annotated pacvar results.

Inspect these expected directories without changing them:

- `annotation/vep/snv`
- `annotation/vep/sv`
- `annotation/vep/cnv`

Inventory candidate `.vcf`, `.vcf.gz`, `.csv`, `.csv.gz`, and `.tsv` files and associate them with samples. Inspect headers and a small number of records to confirm each file's role before selecting it. Do not select inputs only because their filenames resemble an example.

For each sample, locate its SNV `clinvar_pathogenic.csv` and `cosmic.csv` outputs under `annotation/vep/snv`; allow a sample prefix or other pipeline-added text around those suffixes. Generate each SNV table independently when its input exists. If neither exists, skip the SNV report for that sample. If only one exists, generate that report and mark the other unavailable in the index.

Use the applicable VEP-annotated SV input under `annotation/vep/sv` for the general SV and BND-candidate reports. For CNV, first inspect `annotation/vep/cnv`. The current example generator derives depth-supported `DEL`/`DUP` records from a VEP SV VCF using `SVCLAIM=D` and sample `CN`; therefore, if no suitable CNV file exists there, inspect the sample's VEP SV VCF and use it only when those required fields are present. If a report's required input is unavailable or incompatible, skip that report, record the reason, and continue with the other report types.

Before writing anything, summarize the discovered samples, selected source files, reports that can be generated, and reports that will be skipped.

## Create the dashboard layout

Create the following structure under the project directory:

```text
dashboard/
|-- index_<sampleID>.html
|-- cnv_interactive/
|-- snv_interactive/
|-- sv_bnd_candidate/
`-- sv_interactive/
```

Create only the four named report directories and the applicable per-sample files. Put each adapted Python generator beside the HTML it creates. Keep sample-specific outputs distinct when the project contains multiple samples. Use filesystem-safe sample IDs in filenames; preserve the exact biological sample ID in report titles and page content.

Do not overwrite an existing dashboard, generator, or HTML report without first showing the affected paths and asking the user. Preserve unrelated files.

## Adapt and run the generators

Use the corresponding resources under this skill's `scripts/` directory:

- CNV: `scripts/cnv_interactive/make_genome_cnv_tabs.py` and `scripts/cnv_interactive/cytoBandIdeo.hg38.txt.gz`
- ClinVar SNV: `scripts/snv_interactive/make_clinvar_pathogenic_table.py`
- COSMIC SNV: `scripts/snv_interactive/make_cosmic_table.py`
- BND ranking and circos report: `scripts/sv_bnd_candidate/rank_bnd_candidates.py` followed by `scripts/sv_bnd_candidate/make_sv_candidate_circos.py`
- General SV table: `scripts/sv_interactive/make_sv_table.py`
- Integrated page: `scripts/index.html`

For every applicable sample and report:

1. Copy the relevant generator into its matching `dashboard` subdirectory.
2. Edit the copied generator so its input path, output path, sample label, report title, and internal links match the discovered sample and project. Prefer adding explicit command-line arguments when practical instead of leaving sample-specific constants hard-coded.
3. Keep `cytoBandIdeo.hg38.txt.gz` beside the CNV generator. The supplied cytobands and example labels are for GRCh38; verify the project reference build before using them. If the project uses another reference, stop the CNV report and ask for a compatible cytoband resource rather than relabeling the GRCh38 data.
4. Run the generator from a predictable working directory and capture failures. Do not report success merely because a file was created.

The report behavior should be:

- `cnv_interactive`: a chromosome-tabbed, interactive genome CNV report.
- `snv_interactive`: separate searchable tables for ClinVar pathogenic and COSMIC variants.
- `sv_bnd_candidate`: rank qualifying BND/fusion candidates, then create an interactive candidate table with circos visualization for the top-ranked events. Preserve the ranked intermediate table beside the report when the circos generator consumes it.
- `sv_interactive`: a searchable, sortable interactive table for non-BND structural variants.

Generated HTML must be self-contained except for relative links among files inside `dashboard`. Avoid absolute project paths in HTML so the dashboard remains portable.

## Build the sample index

Create `dashboard/index_<sampleID>.html` for every sample by adapting `scripts/index.html`. Replace all example sample names, titles, counts, summaries, highlighted candidates, and paths with values derived from that sample's selected inputs and generated reports. The example contains fixed JRe65 content and must never be published unchanged for another sample.

The index must provide a high-level summary and relative links to every successfully generated report in:

- `cnv_interactive`
- `snv_interactive`
- `sv_bnd_candidate`
- `sv_interactive`

Do not include broken links. Show unavailable report types as unavailable with a short reason, or omit them when that produces a clearer page. Distinguish VCF records, unique variants, and transcript-level annotation rows when presenting counts; do not mix these units.

## Validate the result

Before completion:

1. Run `python -m py_compile` on every copied or edited Python generator.
2. Confirm that every expected HTML file exists, is non-empty, contains the correct sample name, and does not retain `JRe65` or another example-only label unless that is the real sample.
3. Parse or otherwise inspect each generated HTML document for a title and basic document structure.
4. Resolve every local `href` in each sample index and confirm that its target exists beneath `dashboard`.
5. Check that report counts and highlighted variants agree with their source data or generator outputs.
6. Summarize generated and skipped reports per sample, including the reason for every skip, and give the absolute path to each `index_<sampleID>.html`.

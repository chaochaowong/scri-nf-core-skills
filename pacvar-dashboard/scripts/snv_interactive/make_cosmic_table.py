#!/usr/bin/env python3
"""Build the reduced-column, self-contained COSMIC variant table."""

from pathlib import Path

from make_clinvar_pathogenic_table import build_table


INPUT = Path(
    "annotation/vep/snv/"
    "JRe65_Neuroblastoma.snv.phased.vep.cosmic.csv"
)
OUTPUT = Path(
    "downstream/snv_interactive/"
    "JRe65_Neuroblastoma.cosmic.interactive.html"
)
SELECTED_COLUMNS = [
    "CHROM",
    "POS",
    "REF",
    "ALT",
    "HGVSg",
    "HGVSp",
    "Consequence",
    "SYMBOL",
    "Existing_variation",
    "CLIN_SIG",
    "SOMATIC",
    "GT",
    "AD",
]


if __name__ == "__main__":
    build_table(
        INPUT,
        OUTPUT,
        title="JRe65 COSMIC variants",
        search_names=["SYMBOL", "HGVSg", "HGVSp", "Existing_variation"],
        selected_columns=SELECTED_COLUMNS,
    )

#!/usr/bin/env bash

# 1) define Project
PROJECT="HSe111_MOLM12_DOXO-Ida-AZD-ACLA-ActD-6hr_CHM13_Fiberseq_20261011"
PROJECT_ID="HSe111"
ASSOC="sarthy_lab"

# 2) Define common base directories if you like
BASE="/data/hps/assoc/private/${ASSOC}/NGS/FiberSeq_Results/${PROJECT}"
WORKDIR="/data/hps/assoc/private/${ASSOC}/user/${USER}/tmp/${PROJECT_ID}"

# 3) run nf-core/pacvar version 1.1.0
nextflow run nf-core/pacvar -r 1.1.0 \
        -c sasquatch-cpu-pacvar.config \
        -profile sasquatch \
        -w "${WORKDIR}" \
        -params-file "${BASE}/pipeline_params/params.json" \
	-resume

# SCRI nf-core Skills

This repository contains Codex or Gemini skills for preparing and running nf-core pipelines in the Seattle Children's Research Institute (SCRI) Sasquatch HPC environment.

Each supported nf-core pipeline has its own directory and `SKILL.md`. Planned pipeline-specific skills include PacVar, ATAC-seq, and CUT&RUN.

Each skill will guide users through locating or constructing the files and environment required for that pipeline:

1. a mamba environment containing Nextflow;
2. a customized Nextflow configuration for Sasquatch, based on resources such as [`sasquatch-nf-config`](https://github.com/chaochaowong/sasquatch-nf-config);
3. a pipeline-compatible nf-core samplesheet; and
4. a pipeline-specific `params.json` file.

Detailed setup, validation, and execution instructions will be maintained in each pipeline directory rather than in this README.

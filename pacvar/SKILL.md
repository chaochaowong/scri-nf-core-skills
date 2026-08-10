---
name: pacvar
description: Prepare an nf-core/pacvar run on the SCRI Sasquatch HPC cluster. Use when Codex needs to collect PacBio HiFi BAM inputs, build the PacVar samplesheet and Sasquatch Nextflow configuration, create run-pacvar.sh, validate PacVar run files, or guide a user through launching nf-core/pacvar from a mamba environment in tmux.
---

# Prepare PacVar on Sasquatch

Prepare all run files inside the user's existing project directory. Treat that starting project directory as the pipeline output directory; do not create a separate results directory.

## Gather inputs

Confirm the starting project directory, then gather the following information. Ask for missing items together when practical.

- Sample name, absolute HiFi BAM path, and optional absolute BAM `.pbi` path for every sample.
- Sasquatch association (`assoc`) name. Use `sarthy_lab` when the user does not provide one.
- Whether the user has a custom Nextflow configuration. If so, ask for its path or contents.
- A very short project ID suitable for a scratch-directory name.
- The name of the mamba environment containing Nextflow.

Do not guess sample names, BAM paths, the project ID, or the mamba environment. Permit an empty `pbi` value. Check that the project directory and supplied input/config paths exist, and report missing paths before generating dependent files.

## Create the run files

Create `<project-directory>/pipeline_params`. Preserve existing files and ask before overwriting any of the files below.

### Build the samplesheet

Write `pipeline_params/nf-sample-sheet.csv` as a comma-separated file with this exact header:

```csv
sample,bam,pbi
```

Write one row per supplied sample. Use the absolute HiFi BAM and `.pbi` paths. Leave the third field empty when no `.pbi` was supplied. Quote and escape CSV fields correctly when their values require it.

### Build the Nextflow configuration

Write `pipeline_params/sasquatch-cpu-pacvar.config`.

- If the user supplies a custom config, copy it as the starting point.
- Otherwise, download the PacVar template from `https://raw.githubusercontent.com/chaochaowong/sasquatch-nf-config/main/sasquatch-cpu-pacvar.config`.
- Set both `params.assoc` and `params.account` to the selected association name.
- Preserve the template's Slurm `partition` value unless the user explicitly requests another partition. The association/account and partition are different settings; do not replace the partition with the association name.
- Preserve all unrelated custom settings.

### Build the launch script

Use `https://raw.githubusercontent.com/chaochaowong/sasquatch-nf-config/main/run-pacvar.sh` as the starting template and write the result to `pipeline_params/run-pacvar.sh`.

Customize it as follows:

- Set `PROJECT` to the basename of the starting project directory.
- Set `PROJECT_ID` to the user's short project ID.
- Set `BASE` to the absolute starting project directory.
- Set `WORKDIR` to `/data/hps/assoc/private/<assoc>/user/${USER}/tmp/<PROJECT_ID>` using the selected association and project ID. Preserve `${USER}` as a shell variable; do not substitute the current agent's username.
- Keep `--outdir "${BASE}"` because the starting project directory is the pipeline output directory.
- Keep the samplesheet at `${BASE}/pipeline_params/nf-sample-sheet.csv`.
- Make the config path robust to the launch location, preferably by resolving the script's own directory and passing its `sasquatch-cpu-pacvar.config` to `-c`.
- Preserve other pipeline parameters from the template unless the user requests edits.

Make `run-pacvar.sh` executable.

## Validate and review

Before asking the user to run the pipeline:

1. Confirm that the samplesheet header is exactly `sample,bam,pbi`, every row has three fields, every sample name is present, and every supplied path exists.
2. Confirm that the config contains the selected association in both `params.assoc` and `params.account` and that the Slurm partition remains valid.
3. Run `bash -n pipeline_params/run-pacvar.sh`.
4. Confirm that `PROJECT`, `PROJECT_ID`, `BASE`, `WORKDIR`, the config path, the input path, and the output path have the intended values.
5. Check Nextflow with `mamba run -n <environment> nextflow -version`. If it is unavailable, tell the user that Nextflow must be installed in that environment; do not silently choose or modify another environment.

Summarize the generated files and ask the user to inspect everything in `pipeline_params`. Ask whether they want to change any paths, configuration, or PacVar parameters. Apply requested edits and repeat the relevant validation.

## Hand off the run

Do not launch the pipeline on the user's behalf unless they explicitly request it. After the user approves the files, instruct them to open or attach to a `tmux` session, activate the named mamba environment, change to the `pipeline_params` directory, and run:

```bash
./run-pacvar.sh
```

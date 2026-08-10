---
name: pacvar
description: Prepare an nf-core/pacvar run on the SCRI Sasquatch HPC cluster. Use when Codex needs to collect PacBio HiFi BAM inputs, build the PacVar samplesheet and Sasquatch Nextflow configuration, create run-pacvar.sh, validate PacVar run files, or guide a user through launching nf-core/pacvar from a mamba environment in tmux.
---

# Prepare PacVar on Sasquatch

Prepare all run files inside the user's existing project directory. Treat that starting project directory as the pipeline output directory; do not create a separate results directory. Require the project directory to be in Sasquatch association storage under `/data/hps/assoc/` because it becomes `BASE` in `run-pacvar.sh`.

## Gather inputs

Ask the user to provide the starting project directory in Sasquatch association storage under `/data/hps/assoc/`. Do not accept a project directory outside that path; explain the requirement and ask for a valid association-space directory instead. Then gather the following information. Ask for missing items together when practical.

- Sample name, absolute HiFi BAM path, and optional absolute BAM `.pbi` path for every sample.
- Ask: "What is your Sasquatch association (`assoc`) name?" For example, `sarthy_lab`. If the user does not provide a value, tell them that the skill will use the default `sarthy_lab`.
- Whether the user has a custom Nextflow configuration. If so, ask for its path or contents.
- A very short project ID suitable for a scratch-directory name.
- The name of the mamba environment containing Nextflow.
- Ask whether to run the moving `dev` branch or the reproducible `1.1.0` release tag. Default to `1.1.0` when the user has no preference.

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
- If the user provides an association name, edit both `params.assoc` and `params.account` in the config file to that exact value. If the user does not provide one, set both parameters to the default `sarthy_lab`.
- Preserve the template's Slurm `partition` value unless the user explicitly requests another partition. The association/account and partition are different settings; do not replace the partition with the association name.
- Preserve all unrelated custom settings.

### Build the launch script

Use `https://raw.githubusercontent.com/chaochaowong/sasquatch-nf-config/main/run-pacvar.sh` as the starting template and write the result to `pipeline_params/run-pacvar.sh`.

Customize it as follows:

- Set `PROJECT` to the basename of the starting project directory.
- Set `PROJECT_ID` to the user's short project ID.
- Set `BASE` to the absolute starting project directory. Require it to begin with `/data/hps/assoc/`; stop and ask the user for an association-space project directory if it does not.
- Set `WORKDIR` to `/data/hps/assoc/private/<assoc>/user/${USER}/tmp/<PROJECT_ID>` using the selected association and project ID. Require it to remain under `/data/hps/assoc/`. Preserve `${USER}` as a shell variable; do not substitute the current agent's username.
- Set the `-r` argument for `nf-core/pacvar` to the selected revision (`dev` or `1.1.0`).
- Keep `--outdir "${BASE}"` because the starting project directory is the pipeline output directory.
- Keep the samplesheet at `${BASE}/pipeline_params/nf-sample-sheet.csv`.
- Make the config path robust to the launch location, preferably by resolving the script's own directory and passing its `sasquatch-cpu-pacvar.config` to `-c`.
- Preserve other pipeline parameters from the template unless the user requests edits.

Make `run-pacvar.sh` executable for all users:

```bash
chmod a+x pipeline_params/run-pacvar.sh
```

## Validate and review

Before asking the user to run the pipeline:

1. Confirm that the samplesheet header is exactly `sample,bam,pbi`, every row has three fields, every sample name is present, and every supplied path exists.
2. Confirm that the config contains the selected association in both `params.assoc` and `params.account` and that the Slurm partition remains valid.
3. Run `bash -n pipeline_params/run-pacvar.sh`.
4. Confirm that `PROJECT`, `PROJECT_ID`, `BASE`, `WORKDIR`, the config path, the input path, and the output path have the intended values. Verify that both `BASE` and `WORKDIR` begin with `/data/hps/assoc/` and that `WORKDIR` contains the selected association name.
5. Check Nextflow with `mamba run -n <environment> nextflow -version`. If it is unavailable, tell the user that Nextflow must be installed in that environment; do not silently choose or modify another environment.
6. Confirm that `run-pacvar.sh` uses `-r 1.1.0` by default. Because the script runs the remote `nf-core/pacvar` project, do not require a separate pull for this tagged release. If the user selects `-r dev`, remind them that their cached development branch may be stale and that they should consider refreshing it before the run:

   ```bash
   mamba run -n <environment> nextflow pull nf-core/pacvar -r dev
   ```

   Present this as a recommendation rather than running it automatically or requiring it to succeed. Keep `-r dev` in `run-pacvar.sh` when the user selects the development branch.

Summarize the generated files and ask the user to inspect everything in `pipeline_params`. Ask whether they want to change any paths, configuration, or PacVar parameters. Apply requested edits and repeat the relevant validation.

## Hand off the run

Do not launch the pipeline on the user's behalf unless they explicitly request it. After the user approves the files, instruct them to open or attach to a `tmux` session, activate the named mamba environment, change to the `pipeline_params` directory, and run:

```bash
./run-pacvar.sh
```

---
name: fire
description: Prepare, run, and archive the FIRE chromatin-accessibility pipeline on SCRI Sasquatch from nf-core/pacvar fibertools output. Use when Codex needs to locate a fibertools BAM in a pacvar result, install or validate Snakemake, clone or validate the SCRI FIRE repository, create FIRE pipeline_config files, launch FIRE with the Sasquatch Slurm profile, or copy completed FIRE results beside an archived pacvar project on Helen RSS.
---

# Run FIRE on Sasquatch

Collect and validate every required input before creating run files. Keep all pipeline output under the pacvar result directory and all software under the user's SCRI association space. Do not guess identities, paths, samples, or reference names.

## Gather inputs

Ask for all missing values together when practical:

- SCRI association name, such as `sarthy_lab`. If it is not already known from the conversation, ask for it; do not silently default it.
- Absolute pacvar output path.
- Absolute path to a mamba/conda environment containing Snakemake, or confirmation that none exists.
- Existing FIRE repository path in association space and preferred branch, if any. Explain that execution on SCRI must use the `scri` branch even if another branch is preferred elsewhere.
- Absolute reference-genome FASTA path and short reference name, such as `hg38`.
- The absolute Helen active RSS destination where the whole pacvar project was deposited (or will be deposited). Ask for this at the beginning with the other required inputs. This is the parent directory beneath which the completed `FIRE` directory will be copied.

Use the current shell user through `${USER}` in generated commands; do not substitute the agent's username into reusable files.

## Validate pacvar output and select the BAM

1. Resolve the pacvar output with `realpath -e` and require it to be a directory under `/data/hps/assoc/`.
2. Locate its `fibertools` directory case-sensitively first; if absent, report the directories found and ask the user for the correct path. Do not create a fake `fibertools` directory.
3. Find `.bam` files beneath `fibertools`. If there is not exactly one plausible input, show the candidates and ask the user to select one.
4. Require the selected BAM to exist and be readable. Set `BAM` to its canonical absolute path and `BAM_BASENAME` to its filename without `.bam`.
5. Derive `SAMPLE` by removing a terminal `.add_nuc` from `BAM_BASENAME`. Preserve all other characters. For example, `patient01.add_nuc.bam` becomes sample `patient01`; `patient01.bam` remains `patient01`.

The manifest must point to the existing BAM in `fibertools`; do not copy, rename, or manufacture the BAM unless the user separately asks for that operation.

## Ensure Snakemake

If the user supplies an environment path, resolve it and verify it with `<env>/bin/snakemake --version` or an equivalent `conda run -p <env>` command. Also identify the corresponding conda initialization script, normally `<miniforge-root>/etc/profile.d/conda.sh`.

If the user has no environment:

1. Locate `mamba` and its root prefix. Set the intended environment to `<mamba-root>/envs/snakemake_env`, keeping it in `/data/hps/assoc/private/<assoc>/user/${USER}/` when creating a new installation or prefix.
2. Check whether `snakemake_env` already exists and works; never overwrite it.
3. Tell the user the exact prefix and package command, then create the environment named `snakemake_env` with Snakemake from `conda-forge` and `bioconda` after the user confirms the location.
4. Verify `snakemake --version`. Stop and report installation or version-check failures.

Do not proceed to run-file creation until a working Snakemake executable and activation method are known.

## Ensure the FIRE repository

Require the repository to live in association space. For an existing path:

1. Resolve it and verify that it is a Git checkout of `git@github.com:chaochaowong/FIRE.git` (accept the equivalent GitHub HTTPS remote).
2. Inspect the working tree before switching branches. Never discard local changes.
3. Fetch only when needed, then switch to `scri`. If changes prevent switching, stop and ask the user how to handle them.
4. Verify that the active branch is `scri` and that `workflow/Snakefile` and `profiles/slurm-executor` exist.

When no repository path exists, use this default:

```bash
FIRE_PIPELINE_PATH="/data/hps/assoc/private/<assoc>/user/${USER}/.fire"
git clone git@github.com:chaochaowong/FIRE.git "${FIRE_PIPELINE_PATH}"
git -C "${FIRE_PIPELINE_PATH}" switch scri
```

Do not clone over an existing nonempty path. Regardless of another preferred development branch, use `scri` for SCRI execution.

## Validate the reference

Resolve the FASTA with `realpath -e`, require a readable regular file, and retain the user-provided `ref_name`. Check for a usable FASTA index (`.fai`) and report if it is missing rather than silently generating it.

Prefer the canonical resolved FASTA path. If a symlink or storage boundary makes it unusable from compute nodes, explain the issue and ask for an association-space destination before creating a hard link. Confirm that source and destination are on the same filesystem, refuse to overwrite a destination, create it with `ln`, and verify matching inode/device values. If hard-linking is impossible, ask the user whether to copy the FASTA instead; do not make that larger data transfer implicitly. Apply the same explicit handling to required companion indexes.

## Create pipeline configuration

After all prerequisites pass, set:

```text
FIRE_OUTPUT=<resolved-pacvar-output>/FIRE
CONFIG_DIR=<resolved-pacvar-output>/FIRE/pipeline_config
```

Create both directories. Before changing any existing `config.tbl`, `config.yaml`, or `run-fire.sh`, show the conflict and ask whether to overwrite it.

### Create `config.tbl`

Write a tab-delimited file with exactly this header and one data row:

```text
sample	bam
<SAMPLE>	<BAM>
```

Use the derived sample and canonical absolute BAM path. Validate that there are exactly two fields per row.

### Create `config.yaml`

Quote paths and write the canonical reference, reference name, and manifest path followed by these defaults:

```yaml
ref: "/absolute/reference.fasta"
ref_name: hg38
manifest: "/absolute/pacvar/output/FIRE/pipeline_config/config.tbl"
max_t: 24 # Max number of threads to use in very distributed steps
coverage_within_n_sd: 5 # Filter peaks more than x standard deviations from mean coverage
min_contig_length: 0 # default 0
# developer options
min_coverage: 4 # default 4
min_per_acc_peak: 0.25 # default 0.25
min_frac_accessible: 0.0 # default 0.0
keep_chromosomes: "chr[0-9XY]+$"
max_peak_fdr: 0.05 # default 0.05
min_fire_fdr: 0.10 # default 0.10
min_msp: 10 # default 10
min_ave_msp_size: 10 # default 10
```

Replace only the first three example values with the validated values. Preserve `ref_name` as a YAML string if its contents could be interpreted as another YAML type.

### Create `run-fire.sh`

Generate an executable script from this structure, substituting validated absolute paths while preserving `"$@"`:

```bash
#!/usr/bin/env bash

set -euo pipefail

source "/absolute/miniforge3/etc/profile.d/conda.sh"
conda activate "/absolute/miniforge3/envs/snakemake_env"

FIRE_PIPELINE_PATH="/data/hps/assoc/private/assoc/user/${USER}/.fire"
FIRE_OUTPUT="/absolute/pacvar/output/FIRE"

cd "${FIRE_OUTPUT}"

snakemake -s "${FIRE_PIPELINE_PATH}/workflow/Snakefile" \
    --use-conda \
    --profile "${FIRE_PIPELINE_PATH}/profiles/slurm-executor" \
    --configfile "${FIRE_OUTPUT}/pipeline_config/config.yaml" \
    --conda-prefix "/data/hps/assoc/private/assoc/user/${USER}/snakemake-conda-envs" \
    -p -k \
    "$@"
```

Set `FIRE_PIPELINE_PATH`, activation paths, association components, `FIRE_OUTPUT`, and `--conda-prefix` from the collected values. Run from `FIRE_OUTPUT` so FIRE writes there, while using absolute pipeline and profile paths. Apply `chmod a+x`.

## Validate and hand off

Before offering to launch:

1. Recheck the BAM, reference, environment, repository branch, Snakefile, and Slurm profile.
2. Validate `config.tbl` field counts and confirm its sample is the BAM stem with only terminal `.add_nuc` removed.
3. Parse `config.yaml` when a YAML parser is available and confirm `ref`, `ref_name`, and `manifest` exactly match the selected values.
4. Run `bash -n run-fire.sh` and inspect every expanded path.
5. Run a Snakemake dry run from `FIRE_OUTPUT` with the same Snakefile, profile, config, and conda-prefix arguments when doing so will not submit jobs. If the profile makes dry-run submission ambiguous, omit the profile for validation or ask before proceeding.
6. Summarize the three created files and any warnings. Ask the user to review them.

## Launch after approval

Do not launch FIRE until the user explicitly confirms that `pipeline_config/config.tbl`, `pipeline_config/config.yaml`, and `pipeline_config/run-fire.sh` are valid. Treat that confirmation as authorization to run the confirmed `run-fire.sh`; ask again only if files or material paths change afterward.

Immediately before launch, repeat the relevant file, environment, repository-branch, and shell-syntax checks. Run `pipeline_config/run-fire.sh` with `FIRE_OUTPUT` as the working directory, pass through any user-provided arguments, and report the actual command and immediate status. For a long-running run, use the user's requested session mechanism or ask whether they prefer `tmux` or another supported launcher. Report how to inspect or attach to the run. Do not equate successful process or session creation with successful pipeline completion.

## Copy completed FIRE output to Helen RSS

Offer the copy only after verifying from Snakemake's exit status and logs that FIRE completed successfully. Copy only `<resolved-pacvar-output>/FIRE`; do not recopy the entire pacvar project.

Use the user-provided pacvar project destination on Helen active RSS as the parent destination. If that exact path was already recorded during the pacvar workflow, show it when gathering inputs and ask the user to confirm it; otherwise, ask for it at the beginning. Require the path to begin with `/data/rss/helens/`, resolve the nearest existing parent safely, and ensure that the destination corresponds to the same pacvar project. Do not infer a destination merely from matching basenames. If the user cannot provide it initially, record the item as unresolved and do not perform the RSS copy until they supply it.

Set the destination to `<rss-pacvar-project>/FIRE`. Before copying:

1. Show the canonical source and destination and obtain explicit confirmation immediately before this separate data-transfer action.
2. Confirm that `rsync` is available, the source is a directory, and the RSS parent is accessible.
3. If the destination already exists, inspect it and ask whether to merge/update it. Never produce an accidental `FIRE/FIRE` nesting and never delete destination files implicitly.
4. Copy directory contents with semantics equivalent to:

   ```bash
   mkdir -p "/data/rss/helens/path/to/pacvar-project/FIRE"
   rsync -a --info=progress2 \
     "/data/hps/assoc/path/to/pacvar-output/FIRE/" \
     "/data/rss/helens/path/to/pacvar-project/FIRE/"
   ```

5. Check the exit status and compare source and destination file counts and total byte sizes. Report discrepancies; do not claim completion solely from an exit status. Preserve the source and do not use `--delete`.

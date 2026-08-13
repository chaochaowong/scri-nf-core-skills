---
name: pacvar
description: Prepare, launch, archive, and perform downstream analysis of an nf-core/pacvar run on the SCRI Sasquatch HPC cluster. Use when Codex needs to collect PacBio HiFi BAM inputs, build or validate pacvar run files, run nf-core/pacvar from a mamba environment in tmux, copy completed output to Helen active RSS, analyze VEP-annotated VCF files, or use Sasquatch Apptainer/Singularity and R containers for pacvar downstream work.
---

# Prepare pacvar on Sasquatch

Prepare all run files inside the user's existing project directory. Treat that starting project directory as the pipeline output directory; do not create a separate results directory. Before validating or using a user-supplied project path, resolve every symbolic-link component to its canonical physical path. Use that resolved path throughout the workflow because Nextflow on Sasquatch may fail when given a symlinked project path. Require the resolved project directory to be in Sasquatch association storage under `/data/hps/assoc/` because it becomes `BASE` in `run-pacvar.sh`.

## Gather inputs

Ask the user to provide the starting project directory. Resolve it with `realpath -e -- <project-directory>` (or an equivalent canonical-path operation) before performing the `/data/hps/assoc/` check. If resolution fails, report that the directory does not exist and ask for a valid path. If the resolved path differs from the supplied path, tell the user that the symlinked path has been converted to its physical path for Nextflow compatibility. From that point onward, treat the resolved path as the starting project directory: use it for file creation, validation, `BASE`, launch working directories, and user-facing commands. Do not create a hard link; directories generally cannot be hard-linked, and canonical path resolution is the intended operation. Do not accept a resolved project directory outside `/data/hps/assoc/`; explain the requirement and ask for a valid association-space directory instead. Then gather the following information. Ask for missing items together when practical.

- Sample name, absolute HiFi BAM path, and optional absolute BAM `.pbi` path for every sample.
- Ask: "What is your Sasquatch association (`assoc`) name?" For example, `sarthy_lab`. If the user does not provide a value, tell them that the skill will use the default `sarthy_lab`.
- Whether the user has a custom Nextflow configuration. If so, ask for its path or contents.
- A very short project ID suitable for a scratch-directory name.
- The name of the mamba environment containing Nextflow. If the user does not know or does not have one, offer to create the standard environment described below.
- Ask whether to run the moving `dev` branch or the reproducible `1.1.0` release tag. Default to `1.1.0` when the user has no preference.
- Ask whether the user wants to change the launch script's `--genome` parameter. Preserve the template value when they do not request a change.
- Ask for the Helen active Research Storage Server (RSS) destination to which the completed project should be copied. Active Helen paths usually begin with `/data/rss/helens/`. Permit the user to defer this choice, but record the destination before performing a post-run copy.

Do not guess sample names, BAM paths, the project ID, the mamba environment, or an RSS destination. Permit an empty `pbi` value. Check that the project directory and supplied input/config paths exist, and report missing paths before generating dependent files. When an RSS destination is supplied, require it to begin with `/data/rss/helens/` and resolve or validate it without creating a guessed directory hierarchy.

## Ensure a Nextflow environment

If the user does not know which mamba environment to use, first locate mamba and inspect the existing environments. If no suitable environment is found, offer to create `nextflow_25.10_env` with Nextflow 25.10.4, which satisfies the minimum Nextflow version required by nf-core/pacvar 1.1.0.

Ask for explicit confirmation before creating the environment. After approval:

1. Check whether `nextflow_25.10_env` already exists. Do not overwrite or recreate an existing environment.
2. If it does not exist, run the equivalent of:

   ```bash
   mamba create -n nextflow_25.10_env \
     -c conda-forge \
     -c bioconda \
     nextflow=25.10.4 \
     --yes
   ```

   Use the resolved mamba executable path. Do not add unrelated packages.
3. Verify the installed version:

   ```bash
   mamba run -n nextflow_25.10_env nextflow -version
   ```

4. Require the output to report Nextflow 25.10.4. If the existing environment contains a different version, report it and ask whether the user wants to update that environment or choose another one; do not modify it without approval.
5. Use `nextflow_25.10_env` as the selected environment for the remaining validation and launch steps.

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
- Otherwise, download the pacvar template from `https://raw.githubusercontent.com/chaochaowong/sasquatch-nf-config/main/sasquatch-cpu-pacvar.config`.
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
- If the selected revision is `1.1.0` and the user sets `--genome CHM13`, also set `--skip_ensemblvep true`. This is mandatory because the Ensembl VEP integration in pacvar 1.1.0 cannot handle CHM13. Explain that VEP annotation will be skipped for this combination. Use the exact parameter name `skip_ensemblvep`; do not use the misspellings `skip_ensemblvel` or `skip_ensemblvep:`. Do not impose this revision-specific rule on `dev` without first checking the selected revision's current compatibility.
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
5. Locate mamba with `command -v mamba`, confirm the named environment with `mamba env list`, and check Nextflow with `mamba run -n <environment> nextflow -version`. Retain the resolved mamba executable path for the tmux launch. If mamba, the environment, or Nextflow is unavailable, report which item is missing; do not silently choose or modify another environment.
6. Confirm that `run-pacvar.sh` uses `-r 1.1.0` by default. Because the script runs the remote `nf-core/pacvar` project, do not require a separate pull for this tagged release. If the user selects `-r dev`, remind them that their cached development branch may be stale and that they should consider refreshing it before the run:

   ```bash
   mamba run -n <environment> nextflow pull nf-core/pacvar -r dev
   ```

   Present this as a recommendation rather than running it automatically or requiring it to succeed. Keep `-r dev` in `run-pacvar.sh` when the user selects the development branch.
7. If `run-pacvar.sh` combines `-r 1.1.0` with `--genome CHM13`, require `--skip_ensemblvep true` and report an error if it is absent, false, or misspelled.

Summarize the generated files and ask the user to inspect everything in `pipeline_params`. Ask whether they want to change any paths, configuration, or pacvar parameters. Apply requested edits and repeat the relevant validation.

## Launch the pipeline when requested

Do not launch the pipeline until both conditions are satisfied:

1. The user has confirmed that `nf-sample-sheet.csv`, `sasquatch-cpu-pacvar.config`, and `run-pacvar.sh` are correct.
2. The user explicitly asks the agent to run the pipeline.

When both conditions are satisfied:

1. Confirm that `tmux` and the discovered `mamba` executable are available. Re-run the file and environment validations if the files have changed since approval.
2. Use the user-defined short project ID as the tmux session name. Validate that it is safe as a tmux name. Do not kill, replace, or reuse an existing session with that name without asking the user; check first with `tmux has-session -t <PROJECT_ID>`.
3. Create a detached tmux session named `<PROJECT_ID>` with a window named `nextflow`. Start it in `<project-directory>/pipeline_params`.
4. Invoke the user-provided mamba environment and run `./run-pacvar.sh` in the `nextflow` window. Prefer `mamba run` for reliable non-interactive environment invocation. The resulting command should be equivalent to:

   ```bash
   tmux new-session -d \
     -s <PROJECT_ID> \
     -n nextflow \
     -c <project-directory>/pipeline_params \
     'mamba run -n <environment> ./run-pacvar.sh'
   ```

   Use safely quoted literal values and the discovered mamba executable path when constructing the real command.
5. Verify the launch with `tmux has-session -t <PROJECT_ID>`, `tmux list-windows -t <PROJECT_ID>`, and a read-only capture of the `nextflow` pane. Report any immediate error; do not claim that the pipeline is running successfully based only on session creation.
6. Explicitly tell the user that the tmux session name is `<PROJECT_ID>` and the window name is `nextflow`. Provide the command to attach to the session:

   ```bash
   tmux attach -t <PROJECT_ID>
   ```

   Also provide a read-only command for viewing the latest output from the `nextflow` window without attaching:

   ```bash
   tmux capture-pane -p -t <PROJECT_ID>:nextflow
   ```

## Handle completed output

Treat `<project-directory>/annotation/vep` as the standard location for VEP-annotated variant VCF files. Before downstream work or archival, verify from Nextflow's final status and logs that the pipeline completed successfully; a missing tmux session alone does not prove success. If `--skip_ensemblvep true` was used, do not expect VEP-annotated VCFs and explain why the directory or files may be absent.

### Copy the project to Helen

After successful completion, offer to copy the entire project to the previously supplied Helen active RSS destination. Treat this as a separate data-transfer action: show the resolved source and destination and obtain explicit confirmation immediately before starting it. Confirm that GNU `parallel`, `rsync`, the source project, and the destination are accessible. Then run the equivalent of:

```bash
find <project-directory> -type f -print0 \
  | parallel -0 -j 8 --progress rsync -R -- {} <active-rss-destination>
```

Use null-delimited filenames so paths containing spaces or shell metacharacters remain intact. Preserve `rsync -R` so relative source paths are recreated beneath the destination. Do not delete source files. Check the command's exit status, report failures, and do not claim that the copy completed unless all jobs succeeded.

### Perform downstream analysis

Inspect the VCFs under `<project-directory>/annotation/vep` and clarify the requested analysis, expected outputs, reference genome, and sample scope before changing or filtering them. Preserve the original pipeline outputs; write derived files to a clearly named downstream-analysis directory unless the user specifies another location.

Prefer existing software containers over installing tools into the host environment:

- Search `/data/hps/assoc/private/<assoc>/container` for suitable Apptainer or Singularity images. For example, use `/data/hps/assoc/private/sarthy_lab/container` when the association is `sarthy_lab`. Inspect candidate image names and metadata before choosing one; do not assume a similarly named image contains the required tool or version.
- For R or Bioconductor work, look under `/data/hps/assoc/public/bioinformatics/container/R` and prefer `bioconductor_latex_RELEASE_3_19.sif` when it meets the requested package and version requirements. Verify that the image exists and inspect the available R/package versions before analysis. If required packages are absent, explain the gap and agree on a non-destructive installation or alternate image with the user.
- When the user specifically requests deepTools, first search the association container directory for an existing suitable image. If none exists, use the Seqera ORAS image `oras://community.wave.seqera.io/library/pip_deeptools:708076a05ff4636a` and store it under `/data/hps/assoc/private/<assoc>/container`. Confirm the exact output filename and obtain approval before downloading the image. Verify the pulled image and deepTools version before using it.

Use `apptainer` when available and fall back to `singularity`. Bind only the project, required input/reference locations, and output locations needed for the task. Show the user the proposed command before a long-running or output-producing downstream analysis, then validate the resulting files rather than relying only on the container command's exit status.

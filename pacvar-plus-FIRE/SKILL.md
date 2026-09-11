---
name: pacvar-plus-fire
description: Prepare and run nf-core/pacvar followed by FIRE on SCRI Sasquatch, gathering inputs for both pipelines up front and optionally archiving the completed project and FIRE results to Helen active RSS. Use for the combined PacBio HiFi variant-calling and chromatin-accessibility workflow; use the individual pacvar or FIRE skill for only one pipeline.
---

# Run pacvar followed by FIRE on Sasquatch

Execute this as one ordered workflow:

1. Gather and validate the inputs needed by both pacvar and FIRE.
2. Prepare, review, launch, monitor, and verify pacvar.
3. Only after pacvar completes successfully, select its fibertools BAM and prepare, review, launch, monitor, and verify FIRE.
4. Offer the applicable Helen archival transfers after successful completion and with separate confirmation immediately before each transfer.

Do not launch FIRE concurrently with pacvar or merely because the pacvar process or tmux session started. FIRE depends on a successfully completed pacvar fibertools output.

## Required source instructions

Before taking workflow actions, read both sibling skills completely:

- [pacvar instructions](../pacvar/SKILL.md)
- [FIRE instructions](../FIRE/SKILL.md)

Treat those files as the authoritative procedures for their respective stages, including path validation, environment handling, generated files, approvals, launch mechanics, completion checks, and copy verification. Apply this combined skill's ordering and shared-input rules when coordinating them. If either source file is unavailable, stop and report which one is missing; do not improvise the missing pipeline procedure.

## Gather all inputs before preparing either pipeline

Ask for all missing pacvar and FIRE inputs together when practical. Clearly group the questions by shared, pacvar-specific, and FIRE-specific values so the user can answer in one response. Do not ask again for a value that is already known or can be safely derived as specified below.

### Shared inputs

- Sasquatch association name. The pacvar instructions permit `sarthy_lab` as their stated default when the user omits it; use the same selected association for FIRE. Do not independently choose a different FIRE association.
- Absolute starting pacvar project directory. Resolve it to its canonical physical path and require it to be under `/data/hps/assoc/`, as required by the pacvar instructions. This directory is both the pacvar output directory and the parent of the FIRE output directory.
- Helen active RSS destination for the pacvar project. It must begin with `/data/rss/helens/`. The user may defer it, but no copy may occur until it is supplied and validated.

The Helen destination for the completed FIRE directory is the same pacvar project destination. Do not ask for a second unrelated RSS path and do not infer one from basenames. FIRE will be copied to `<rss-pacvar-project>/FIRE`.

### Pacvar inputs

- Sample name, absolute PacBio HiFi BAM path, and optional absolute `.pbi` path for every sample.
- Custom Nextflow configuration path or contents, or confirmation that the standard configuration should be used.
- Short project ID suitable for the scratch directory and tmux session.
- Mamba environment containing Nextflow, or confirmation that a suitable environment must be located or created.
- nf-core/pacvar revision: reproducible `1.1.0` by default or moving `dev` branch.
- Desired `--genome` value, or confirmation that the launch template value should remain unchanged.

### FIRE inputs

- Mamba/conda environment containing Snakemake, or confirmation that a suitable environment must be located or created.
- Existing FIRE repository path in association space and preferred branch, if any. Recommend the `scri` branch because it contains the expected Sasquatch workflow and Slurm profile. If no repository exists, use the FIRE skill's default association-space location after validation.
- Absolute reference-genome FASTA path and short reference name, such as `hg38`.

Do not ask for an existing pacvar output path or fibertools BAM: this combined workflow produces them. Set the future pacvar output to the resolved starting project directory and derive the FIRE input from that completed output. Do not ask the user to predict the exact generated BAM filename during intake.

Validate every input that can be checked before creating files. An unresolved Helen destination does not block computation, but record it and do not perform either archival transfer until it is resolved. Missing required compute inputs block preparation of the dependent stage.

## Stage 1: run pacvar

Follow the complete pacvar instructions using the values gathered above.

Prepare and validate the pacvar samplesheet, Sasquatch configuration, launch script, Nextflow environment, revision, paths, and special genome/revision rules. Preserve existing files and request confirmation before overwriting conflicts.

Present the generated files for review. Do not launch pacvar until the user has both confirmed the files are correct and explicitly asked to run the combined workflow or pacvar stage. Initial permission to run the combined workflow counts as the request to launch pacvar after the generated files have been reviewed, but it does not waive the required file review or authorize altered files that have not been shown.

Launch pacvar using the validated tmux and mamba procedure in the pacvar instructions. Report how to attach and inspect output. Monitor or inspect the run as requested, but do not equate tmux session creation, disappearance, or an idle process with pipeline success.

### Pacvar completion gate

Before proceeding to FIRE:

1. Verify successful completion from Nextflow's final status and logs.
2. Confirm the expected pacvar outputs exist under the canonical project directory.
3. Locate the `fibertools` directory and enumerate readable `.bam` files beneath it using the FIRE selection rules.
4. If there is exactly one plausible FIRE input BAM, select it. If there are zero or multiple plausible BAMs, report the findings and ask the user to identify the intended input; do not guess.
5. Derive the FIRE sample name by removing only a terminal `.add_nuc` from the selected BAM stem.

If pacvar fails or completion cannot be established, stop the transition and report the evidence. Diagnose or retry only within the authorization given by the user. Never launch FIRE against partial pacvar output.

## Stage 2: run FIRE

After the pacvar completion gate passes, set:

```text
PACVAR_OUTPUT=<canonical-pacvar-project-directory>
FIRE_OUTPUT=<canonical-pacvar-project-directory>/FIRE
FIRE_BAM=<selected-readable-BAM-under-fibertools>
```

Follow the complete FIRE instructions using the inputs gathered at the beginning and the values derived from the completed pacvar run. Revalidate inputs that may have changed during the pacvar run, including the reference, Snakemake environment, FIRE repository and branch, Snakefile, Slurm profile, selected BAM, and Helen destination when supplied.

Prepare and validate `FIRE/pipeline_config/config.tbl`, `config.yaml`, and `run-fire.sh`. The manifest must reference the existing canonical fibertools BAM directly; do not copy, rename, or manufacture it. Preserve existing FIRE files and request confirmation before overwriting conflicts.

Present the three generated FIRE files for review. Do not launch FIRE until the user explicitly confirms that they are valid. A request to run the full combined workflow establishes the user's intent to proceed to FIRE after pacvar, but it does not waive this post-pacvar review because the exact generated BAM and FIRE files were not available at initial intake. If material paths or files change after approval, obtain confirmation again.

Launch FIRE only through the validated FIRE procedure. Report its actual launch status and how to inspect the run. Verify successful completion from Snakemake's exit status and logs before describing the combined workflow as complete.

## Archive to Helen

Archival is separate from pipeline execution. Never treat an initial request to run both pipelines as confirmation to transfer data.

After pacvar completes successfully, the pacvar instructions allow offering a copy of the entire project to Helen. In this combined workflow, prefer waiting until FIRE also completes so the project transfer can include the finished `FIRE` directory in one coherent archive. If the user wants pacvar archived before FIRE finishes, follow the pacvar copy procedure, then later offer the separate FIRE update described below.

Immediately before a transfer, show the canonical source and exact destination and obtain explicit confirmation.

- To archive the whole completed combined project, follow the pacvar copy procedure with the canonical pacvar project as source and the validated Helen pacvar-project destination as destination. Verify all transfer jobs as required by the pacvar instructions.
- If the pacvar project was already copied before FIRE completed, copy only `<pacvar-project>/FIRE/` to `<rss-pacvar-project>/FIRE/` using the FIRE copy procedure. Avoid `FIRE/FIRE`, do not use `--delete`, preserve the source, and compare file counts and total byte sizes.

If the Helen destination already contains data, inspect it and ask how to handle the update as required by the applicable source instructions. Do not silently merge, overwrite, or delete destination content.

## Completion report

Report the two stages independently and then the overall outcome:

- pacvar revision, canonical project path, completion evidence, and selected fibertools BAM;
- FIRE repository branch, output path, and completion evidence;
- whether Helen archival was completed, deferred, declined, or encountered discrepancies.

Do not claim the combined workflow is complete unless both pacvar and FIRE have independently passed their completion checks. A deferred or declined optional Helen copy does not make the compute workflow incomplete, but state its status clearly.

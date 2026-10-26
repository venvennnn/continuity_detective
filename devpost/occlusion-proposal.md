---
doc: implementation-proposal
status: approved
---

# Occlusion assessment after the first analysis slice

The approved wardrobe workflow's automatic quality checks have a measured limitation: pose visibility and person segmentation do not reliably detect an object covering clothing. A simulated foreground object passed those checks. Sharpness improvements fix smooth-fabric false rejection but cannot solve this semantic ambiguity.

The actual supplied take1/take2/take3 sequence now supports the core reference behavior: both later takes differ from take1; after declaring take2 the new reference, take2 no longer differs and take3 still does. These results do not establish reliable occlusion detection.

## Recommended small product adjustment — accepted on resuming the build

- Keep automatic blur, size, visibility, exposure and ambiguity checks, with explicit reasons and provisional calibration labels.
- Add an explicit **Not assessable** action in evidence review, with reasons **Occluded**, **Blurred**, and **Ambiguous**. It records human assessment separately from the normal finding disposition.
- Human not-assessable status removes a result from actionable continuity errors and ordinary no-difference results. Preserve the original computed measurement and automatic outcome in the audit record; do not fabricate, rewrite or hide evidence.
- Export the automatic assessment, human assessment/reason, and effective review status separately. Do not export a human-unassessable result as a confirmed match or error.
- Label automatic visibility checks as limited and require human review; no claim of validated general automatic occlusion handling. A future occluder/garment model would need independent validation.
- Keep the supplied real-clip reference demonstration and all other approved product behavior.

The learner instructed proceeding with the workbench after this proposal and additionally requested combined sequence playback. If accepted, update the affected PRD/spec quality/review/export sections and checklist before continuing to the workbench slice. The first slice remains unchecked until this known capability gap is resolved by an agreed method/boundary.


---
doc: checklist
status: approved
---

# Build Checklist

Build mode: fast — selected in line with the learner's request for fewer questions; planned hands-on checkpoints remain required.

Current state: The workbench and combined sequence player are implemented and running on port 5174. Slice 2 mechanical checks and integrated review/persistence/export checks pass; the planned early learner hands-on feedback is pending. Do not mark that feedback complete until the learner reports back. Slice 3 implementation is present but its learner check/final verification remain to be recorded after feedback.

## Slices

- [x] **1. Inspect real wardrobe evidence and prove forward reference changes**
  Becomes usable: A runnable local inspection command takes real short clips and confirmed reference positions/crops, writes actual A/B evidence and quality outcomes, and demonstrates that a new reference affects only its forward segment.
  Why now: Independently proves the critical model, media, quality and measurement risks before UI polish. The unique kernel is exercised here, rather than postponed until the final integration.
  PRD ref: `prd.md > Analysis and Evidence Inspection`, `prd.md > Reference Changes, Correction, and Undo`, `prd.md > States and Boundaries`.
  Spec ref: `spec.md > Frame Extraction and Torso Proposal`, `spec.md > Quality Gate and Wardrobe Measurement`, `spec.md > Reference Resolver and Result Reconciliation`, `spec.md > Verification and Capability Gate`.
  Build: Bootstrap the Python environment, compatible pinned dependencies, model fetch/provenance, media extraction, pose proposals, crop correspondence, quality gates, measured colour distance, and reference resolver. Add a runnable inspector under backend/scripts that saves evidence and a machine-readable report using the same analysis code the worker will use. Use real footage with provenance for validation; synthetic fixtures are only deterministic plumbing tests. Add source mapping/reference boundary tests. Keep thresholds provisional until calibrated. If a required capability fails, fix it or discuss an explicit method/scope revision before proceeding; do not mark real-footage validation complete without evidence.
  Verify (mechanical): Clean environment imports and model load succeed; inspect real decoded frames and source timestamps, crops, measured scores, and quality reasons. Test before/at/after reference boundaries, unchanged earlier associations, and a later unwanted difference against the new reference. Check clear unchanged/changed wardrobe plus blur, occlusion and ambiguity cases; record outcomes and limits in validation/report.md. If real footage is unavailable, leave the gate pending rather than passing it with fabricated evidence.
  Learner check: Run the inspector on your short sequence and inspect the saved A/B images/report: confirm the clothing crop is meaningful and the forward reference change matches the intended sequence. In fast mode, these outputs are available for the early checkpoint after slice 2; a capability failure is raised immediately.
  Commit: `Prove wardrobe evidence and forward reference comparisons`

- [ ] **2. Import clips, confirm a reference, inspect findings and declare a new wardrobe**
  Becomes usable: The styled browser workbench imports and orders clips, proposes a reference, allows frame/crop correction, runs the separate worker after confirmation, displays clickable A/B evidence, and confirms a forward reference change with re-scored results.
  Why now: Wraps the proven analysis kernel in the complete visible core loop. Early hands-on feedback can still shape review and persistence work.
  PRD ref: `prd.md > Screens and Layout`, `prd.md > Look and Feel`, `prd.md > Import and Sequence Order`, `prd.md > Initial Reference Confirmation`, `prd.md > Analysis and Evidence Inspection`, `prd.md > Reference Changes, Correction, and Undo`.
  Spec ref: `spec.md > Workbench and Project Controller`, `spec.md > Shot List and Timeline`, `spec.md > Reference Editor`, `spec.md > Local API and Media Store`, `spec.md > Analysis Worker and Queue`, `spec.md > Evidence Players and Findings Panel`, `spec.md > Local API Contracts`, `spec.md > Look and Feel`.
  Build: Bootstrap React/TypeScript/Vite inside this usable slice, implement the reference-derived layout, FastAPI upload/media/job endpoints, SQLite queue and separate worker. Add source seeking/exact frame extraction, manual selection/crop fallback, confirmation-before-analysis, measured findings/quality states, both evidence players, timeline boundaries, and new-reference confirmation/re-scoring. Guard revisions so late results cannot replace current state. Document exact startup commands.
  Verify (mechanical): Run API, worker and frontend; frontend type/build checks pass. Exercise real import/order/proposal/crop/confirm/analyse/select finding/change reference/re-score in the browser. Assert no comparison before confirmation, exact evidence metadata and both player seeks, old reference before the boundary, new reference at/after it, and a subsequent difference still flagged. Inspect desktop and narrow-screen layout, crop letterboxing and empty/no-person states. Exercise a worker-offline/error path without invented results.
  Learner check: Start the three local processes and open http://127.0.0.1:5174. Import your clips, correct/confirm the reference, inspect a finding, and declare a new wardrobe. Tell me what felt wrong, confusing, or unlike the supplied design. Resolve feedback before proceeding.
  Commit: `Add reference-aware video inspection workbench`

- [ ] **3. Review findings, correct or undo references, resume and export**
  Becomes usable: The creator can disposition findings, correct/undo reference changes, close and resume the local project, relink missing media, and export portable evidence with reference and review history.
  Why now: Completes the editor handoff around the exercised core loop without allowing persistence or review decisions to corrupt comparison behavior.
  PRD ref: `prd.md > Review Decisions`, `prd.md > Reference Changes, Correction, and Undo`, `prd.md > Local Save and Resume`, `prd.md > JSON Export`, `prd.md > States and Boundaries`.
  Spec ref: `spec.md > Workbench and Project Controller`, `spec.md > Reference Resolver and Result Reconciliation`, `spec.md > Reference Editor`, `spec.md > Persistence and JSON Export`, `spec.md > Data Model`.
  Build: Add per-finding dispositions, historical/superseded results, current-forward-reference correction and undo snapshots. Implement IndexedDB project/thumbnail persistence, source availability checks and hash-verified relinking, save-failure visibility, explicit manual rerun, and JSON export with embedded evidence images and reference-event log. Unchanged evidence retains decisions; changed evidence receives fresh review. No cloud accounts, still-image reference uploads, repair, regeneration, PDF or CSV.
  Verify (mechanical): Browser checks confirm a dismissed finding does not suppress future differences; changed evidence does not inherit old decisions, unchanged evidence retains them, undo restores scores/references/decisions, and stale revisions cannot be exported as current. Reload without automatic analysis, restart local services, relink an absent source and reject a wrong same-name file. Parse exported JSON and inspect embedded evidence, source positions/crops, quality outcomes, current/historical labels and reference applicability outside the running session. Check storage/export failure messages.
  Learner check: Mark findings with different decisions, change then undo a reference, close/reopen the app, and export JSON. Confirm the sequence, references, findings and decisions survived and the export explains the evidence you reviewed.
  Commit: `Persist review history and export wardrobe evidence`

- [ ] **4. Validate the complete short-video workflow and prepare it for final review**
  Becomes usable: A verified local proof of concept with reproducible setup, documented detection limits, robust failure states and the real-footage one-minute demonstration path ready for the learner's final exploration.
  Why now: End-to-end evidence now covers the complete product, so remaining media/quality/navigation issues can be fixed against actual interactions rather than inferred from isolated functions.
  PRD ref: `prd.md > The Core Journey`, `prd.md > States and Boundaries`, `prd.md > What We're Building`.
  Spec ref: `spec.md > Verification and Capability Gate`, `spec.md > Important Failure Modes`, `spec.md > Where It Runs and How Someone Tries It`.
  Build: Run the full labelled real-footage validation and repair remaining failures. Cover portrait/rotated and variable-frame-rate media, blur/occlusion/ambiguity, missing source/model/worker, stale runs and no-drift results. Keep analysis coverage and limits visible. Finish README setup/demo instructions and validation/report.md. Verify that excluded detector categories/actions did not enter the product. Do not mark unsupported capabilities validated or hide unresolved quality failures.
  Verify (mechanical): Run the planned pytest suite, frontend production build, and the main Playwright workflow. Re-run only relevant tests after fixes. Execute all approved demo beats with actual footage and inspect the exported findings against source evidence. Start from documented commands and check the visible workbench. Record real measured results, pending limitations and any plan changes; no synthetic-only validation claim.
  Learner check: Explore the app freely using the full one-minute scenario and awkward inputs. Report what is broken, confusing or worth changing, then retry agreed fixes. Explicitly confirm readiness only when the final feedback is resolved.
  Commit: `Validate complete wardrobe inspection workflow`

## Hands-on Checkpoints

- [ ] Early usable behavior explored — after slice 2, inspect real wardrobe evidence and try reference confirmation/change before the remaining review/persistence work; resolve learner feedback.
- [ ] Final kick-the-tires exploration and feedback completed — after slice 4; learner tries the complete loop and awkward inputs.

## Final Review

Record agreed fixes here as unchecked tasks, then implement, verify, commit and have the learner retry. No changes needed is a valid outcome. Final review is not complete solely because automated checks pass.

- [ ] Final review complete — feedback resolved and learner confirms ready to ship

## Code Tour and App Map

- [ ] Learning activity complete — focused investigation of how one actual reference event changes later comparison inputs while a finding annotation does not; use completed build practice if it already covers this.
- [ ] Optional edit and transfer reflection addressed — offered/declined/already covered/not applicable as appropriate.
- [ ] `devpost/app-map.html` generated from finished code, checked, and shown, including a project-grounded practice to reuse.

Activity and evidence: Pending; record actual code/tests/observations after final revisions, not assumed learning.
Route and stops: Pending actual implementation; connect reference event, resolver and result reconciliation using real symbols.
Edit outcome: Not yet offered; optional, not a requirement to change working code.
Reflection: Not yet offered; personal answer belongs only in the ignored learner profile.
Activity mode: Planned focused alternative for a plan-first learner; reuse genuine practice from the build where appropriate.

## Revisions

- Use opencv-contrib-python as the single OpenCV distribution — the installed MediaPipe release depends on it; overlapping opencv-python was removed and pip check passes. Added a runnable inspector/report companion under backend/scripts for the planned first analysis-risk slice; this does not change the product workflow.

- Seated subjects and smooth white fabric exposed proposal/focus failures — use upper-torso geometry and strongest-edge focus measurement, evaluate the exact proposed rectangle, and include effective mask/quality provenance in comparison fingerprints. Actual take1/take2/take3 transition checks and twelve tests pass. Synthetic foreground occlusion still passes automatic gates; proposed human Not assessable review requires agreement before changing that capability boundary. Slice 1 remains incomplete pending resolution.

- The learner instructed proceeding with the website after the occlusion proposal and requested combining all three takes. Accept human Not assessable review, preserving automatic evidence and limited visibility claims. Add an actual merged sequence video, source-offset mapping, in-video finding annotations and timeline seek-to-finding navigation to slice 2; preserve source evidence timestamps.


- The first visible workbench naturally shares one project reducer across reference confirmation, review, undo and saving. Implemented that integration together so early hands-on review uses the complete real sequence rather than a throwaway UI. This preserves the remaining learner checkpoints; no unperformed hands-on check is marked complete. The local preview uses 5174 because the earlier application occupies 5173.


- Verified workbench checkpoint: 21 backend tests, two browser integration tests, TypeScript/production build and lint pass. Actual combined playback is 24 seconds with cut offsets 8 and 16 seconds. Tested reference replacement, initial reference correction, undo, per-sample decisions/assessment, reload without analysis, cached previews with API unavailable, portable JSON, and mobile overflow. Fixed a save-status race so Saved locally refers to the exact written snapshot. The early learner hands-on checkpoint is now pending; automated tests do not substitute for it.

- Early hands-on feedback requested more apparent wardrobe differences directly in the video. Added prominent evidence-derived Grey → White and White → Red callouts, representative colour swatches and desktop before/after crop close-ups; retained the active-reference label separately from the adjacent-cut comparison. Overlay updates follow completed seeks and remain within the playing clip. Compact mobile treatment preserves the subject view. User retry is pending.

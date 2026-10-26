---
doc: prd
status: approved
---

# Continuity Detective — Product Requirements

A local video inspection workbench for creators assembling short videos, proving wardrobe-reference consistency for one subject using real footage and explicit creator intent.

Source: `scope.md > Who It's For`, `The Unique Kernel`, and `The POC Boundary`.

## The Core Journey

1. Import two or three short clips and establish their sequence order.
2. Inspect the automatically proposed earliest clear reference frame and torso crop. Confirm or correct the frame and crop before analysis begins.
3. Analyse the sequence and inspect computed differences, explicit assessment limitations, and timestamped A/B evidence.
4. Record review decisions or explicitly confirm a new wardrobe reference from a selected sequence position.
5. Re-score with the appropriate reference for each position. Earlier frames retain their earlier reference; a subsequent unwanted difference remains detectable against the new one.
6. Export all findings and decisions as JSON. Close and return to the locally saved sequence without automatic re-analysis.

Source: `scope.md > The Core Loop` and `What “Working” Looks Like`.

## Screens and Layout

Use one workbench with a reference-confirmation surface and an analysis/results surface. Keep the shot list, large A/B evidence frames, timeline/filmstrip, and findings panel central to the experience.

Reference confirmation shows a large candidate frame, a semi-transparent torso crop with draggable edges, the imported-clip filmstrip with the selected frame highlighted, and **Use this reference** / **Choose different frame** actions. The filmstrip remains clickable. **Reset crop** restores the automatic proposal where one exists.

Results retain a persistent **Wardrobe reference** thumbnail and starting-position label. Selecting it opens the reference editor. Timeline markers show reference boundaries. Finding selection opens both source moments in the evidence players.

First use shows an import entry point without fabricated clips, scores, or findings. Restored projects offer **Continue last sequence** or restore directly. Exact responsive layout and visual implementation belong in the spec.

Source: `scope.md > Inspiration & Identity`, plus the reference-confirmation interview.

## Look and Feel

Follow a white one-page studio: charcoal typography, thin dividers, restrained red annotations, a horizontal shot reel, large A/B frames, timeline, and findings panel. Use generous display type, quiet motion, and clear text labels alongside any status colours/icons. Do not copy hard-coded percentages, detections, sharing actions, or regeneration controls from the supplied visual reference.

Source: `scope.md > Inspiration & Identity`.

## Features and Behavior

### Import and Sequence Order

Import local clips and allow the creator to establish their order. Reference applicability follows that order and a precise position within a clip, rather than recording time. Show imported clips in the shot list and filmstrip.

Acceptance:

- The creator can see and establish clip order before confirming a reference.
- Evidence identifies its source clip and source position as well as its place in the sequence.
- An unusable clip is identified visibly; it must not generate invented results or prevent selection of another usable clip.

Source: `scope.md > The Core Loop`.

### Initial Reference Confirmation

Automatically propose the earliest sufficiently clear frame containing a detectable person and a torso crop. The creator described a face box expanded downward as the proposal approach; validate its suitability in the technical plan rather than treating it as evidence of accurate torso detection.

No continuity analysis runs before **Use this reference**. The creator can select another filmstrip frame, resize the crop, and confirm. The confirmed frame and final crop become the reference. The selected thumbnail remains visible in results.

If no suitable automatic candidate exists, show **“No clear person found for a wardrobe reference.”** Keep the filmstrip visible, with guidance: **“Select a frame where the subject’s torso is visible, then adjust the crop if needed.”**

Manual selection may propose a crop around a detected person or a large central rectangle if no person is detected. Identify the latter as a manual selection aid, not a detected torso. Allow adjustment and explicit confirmation. **Skip auto-reference and pick manually** uses this same editor; no separate upload workflow is required.

Acceptance:

- Selecting another frame updates the candidate preview and crop.
- Crop corrections are included in the confirmed reference.
- Automatic failure never invents a detected crop or starts analysis.
- Manual confirmation does not force an unusable region to pass quality assessment.

Source: `scope.md > What “Working” Looks Like` and `The POC Boundary`.

### Analysis and Evidence Inspection

Compute wardrobe comparisons against the reference applicable at each analysed position. Show keyframe thumbnails, an explained computed difference score, and supported descriptions such as a colour difference only when the analysis substantiates them. A difference score is not automatically a probability or confidence percentage.

Each finding links to actual reference and comparison frames, source clips, exact positions, and crop geometry. Clicking a finding seeks both evidence players to their respective recorded moments. The players may be at different positions in different clips; do not assign a shared timestamp to distinct evidence.

Show **not assessable** with a reason when blur, occlusion, small subject size, or ambiguity prevents a supported comparison. These results are distinct from both a match and an unwanted difference, remain visible, and are included in export.

Acceptance:

- An unchanged, usable wardrobe and a visible wardrobe difference produce appropriate results on real footage.
- A finding's displayed images, crop, reference version, and timestamps agree with the computed evidence.
- Clicking the finding navigates both players to those evidence positions.
- Unusable evidence does not appear as a match or a confident wardrobe error.
- No finding depends on canned detections or unsupported garment/material labels.

Source: `scope.md > The Unique Kernel`, `What “Working” Looks Like`, and `The POC Boundary`.

### Review Decisions

A detected actionable difference initially appears as **Needs fix**. The creator may change its disposition to **Intentional (keep current reference)**, **False positive**, or **Defer / review later**. Show the recorded decision in the list and preserve it with the finding. Defer remains open; Intentional and False positive dismiss only that individual result.

These dispositions do not change thresholds, suppress similar future findings, or change reference selection. **Needs fix** is an editing handoff, not an automatic repair operation. Quality outcomes such as not assessable remain separate from the creator's disposition.

Acceptance:

- Decisions are visible, editable, persisted, and included in export even for dismissed findings.
- Marking one finding Intentional or False positive leaves future comparisons unchanged.

Source: `scope.md > The Core Loop` and `Explicitly Cut`.

### Reference Changes, Correction, and Undo

From any selected sequence frame, **New wardrobe from here** opens a confirmation preview with the current crop, the prompt **“Set as new wardrobe reference from this frame onward?”**, an exact timeline start marker, and **Confirm new reference** / **Cancel**.

Confirming preserves the earlier reference for preceding frames and applies the new frame/crop from the selected position onward. Re-score and refresh findings. Show which reference is in force and retain the change event linked to its originating finding, if any. The intentional transition is accepted or no longer unresolved after recomputation; later unwanted drift is still evaluated against the new reference.

The persistent reference control opens the editor to correct the current forward reference's start frame and crop. Confirmation replaces that forward reference, preserving the earlier reference for the preceding segment. **Undo last reference change** restores the previous reference state, starting point, and prior scores; this is not arbitrary project version history.

Acceptance:

- Cancel leaves reference state and results unchanged.
- Confirm shows the exact reference boundary and updates affected comparisons.
- Earlier positions retain their prior reference association.
- Correcting the current forward reference updates its frame/crop and boundary explicitly.
- Undo restores the prior reference configuration and associated scores.

Source: `scope.md > The Unique Kernel` and `What “Working” Looks Like`.

### Local Save and Resume

Persist the last project's clip identities/order, thumbnails, crop coordinates, reference frames and boundaries, ordered reference-change log, results, and all review decisions locally. No account, cloud sync, or multi-device access.

On return, restore the project without automatically re-running analysis. If original clips cannot be reopened, keep saved thumbnails, references, results, and decisions visible and request that the creator reselect the same files. Offer manual **Re-run analysis** when the required media is available. Do not claim that an old temporary media URL can itself restore a file.

Acceptance:

- Closing and reopening retains reference history, results, and decisions.
- Missing source media is clearly indicated without erasing saved work.
- Reopening does not silently recompute or alter decisions.

Source: `scope.md > The Core Loop`, elaborated by the persistence interview.

### JSON Export

Export all findings, including dismissed and deferred findings, plus not-assessable outcomes. Include:

- Project/sequence identifier and export timestamp.
- Finding ID, wardrobe category, computed difference/severity score when assessable, its meaning, and a supported description.
- Both source clip identifiers and exact timestamps/frame positions; interval endpoints when an interval is reported.
- Reference/comparison thumbnails or usable thumbnail references, crop coordinates, and reference version used for that comparison. Thumbnail references must remain interpretable outside the open session.
- Creator decision and, where applicable, the start frame/time of **New wardrobe from here**.
- Current reference summary and ordered reference-change events, sufficient to understand which reference applied at each compared position.
- Explicit assessment status and reason; do not fabricate a numeric severity for an unassessable comparison.

Acceptance: Exported JSON is readable independently of the running UI and explains the evidence and creator decisions without requiring the original analysis session. Source media may still be needed for playback; the export does not imply that full videos are embedded.

Source: `scope.md > What “Working” Looks Like` and `The POC Boundary`.

## States and Boundaries

- **Empty:** Import prompt; no sample results presented as real analysis.
- **Awaiting reference:** Candidate or explicit automatic-selection failure; analysis waits for confirmation.
- **Analysing/re-scoring:** Visible progress; old results must not appear to describe a newly applied reference before recomputation succeeds.
- **Complete with no drift:** State that no differences were flagged among assessed samples; distinguish any not-assessable regions. Do not imply every video frame was checked unless it was.
- **Not assessable:** Explicit quality/ambiguity reason, distinct from pass/fail.
- **Media unavailable:** Saved project stays inspectable; playback/re-analysis requests source relinking.
- **Analysis failure:** Visible failure and recovery path; preserve references and decisions rather than displaying invented success.
- **Changed inputs:** Results derived from obsolete sequence order, crop, or reference state must be distinguished from current results. Unchanged findings retain decisions. If reference or compared evidence changes, preserve the old finding and decision as historical, and create a fresh current result. A new actionable difference starts as Needs fix; an unassessable result retains its explicit assessment status. Historical results are labelled superseded, excluded from the current actionable list, and retained in export with their reference/evidence context. Undo restores the prior results and their decisions.

## Product Decisions

- One subject in short videos, with one active wardrobe reference at a given sequence position, keeps the proof focused.
- Automatic reference proposals always require creator confirmation; manual frame/crop correction provides the fallback.
- Explicit forward reference changes express intent; the system does not infer off-screen causal events.
- Intentional and False positive apply only to one finding; no learned suppression or threshold changes.
- Local persistence preserves the last sequence without accounts or automatic re-analysis on reload.
- JSON is the required handoff. PDF/CSV and still-image uploads are deferred to keep one complete loop.
- Review planning documents in Markdown.

## What We're Building

A complete import → reference confirmation → computed wardrobe analysis → timestamped evidence → review → explicit reference change/re-score/undo → local resume → JSON export workflow, validated using the real-footage demo in `scope.md > What “Working” Looks Like`.

## Deferred From the POC

Prop/face checks require independent validation. Script metadata, branching story graphs, separate garment-layer state, progressive damage accumulation, and automatic narrative-intent reasoning exceed this single-subject proof. Still-image reference upload and PDF/CSV export add paths not needed for the demonstrated loop. Cloud sync, accounts, multi-device use, and project version history beyond the linear reference log are excluded.

## Non-Goals

No automatic repair, inpainting, regeneration, copied sharing controls, fabricated scores, or unvalidated lighting/eyeline/facial detections. No claim that colour difference alone proves an outfit change or narrative error.

## Open Questions

- No unresolved product decisions block this draft. Changed evidence receives fresh review; prior decisions remain with historical evidence. Unchanged findings retain decisions.
- **Technical investigation in 4-spec:** Supported media limits, automatic person/torso proposal, candidate-frame sampling, quality assessment, difference metric/calibration, local media persistence, and portable thumbnail representation. These are feasibility questions, not implemented capabilities. Assess against the curriculum's 2–4-hour target and revisit scope if needed.

## Accepted Build Revision — Combined Sequence Review

The learner requested combining take1/take2/take3 into one video and showing continuity misses directly when they occur. Implement actual concatenated sequence playback with source-to-sequence offset mapping, timeline markers, and in-video annotations tied to computed sampled evidence. Clicking a finding seeks the combined player and A/B evidence to the correct positions. The video itself is not permanently burned with unsupported annotations; dynamic annotations use computed evidence and disclose sampling. Preserve the original files.

The learner instructed proceeding after the occlusion proposal. Include explicit human Not assessable review reasons (Occluded, Blurred, Ambiguous), separate from finding disposition. Preserve automatic measurements in audit/export and mark effective human-unassessable outcomes accordingly. Automatic occlusion detection remains limited and unvalidated; no claims otherwise.

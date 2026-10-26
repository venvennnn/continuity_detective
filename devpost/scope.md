---
doc: scope
status: approved
---

# Continuity Detective

A video inspection workbench for creators assembling short videos from ordered clips, starting with wardrobe continuity for one subject.

## The Unique Kernel

Computed visual differences are interpreted against a creator-declared wardrobe state. “New wardrobe from here” creates a new reference for subsequent frames while preserving the earlier reference for preceding frames. Intentional changes stop producing unresolved drift findings, and later unwanted differences must still be detected against the new reference.

## Who It's For

A creator assembling short-form videos from AI-generated shots, using footage of the same person across a small sequence. Phone footage is also suitable for demonstrating the workflow. They need evidence they can inspect and decisions they can control; the current review process has not been established.

## The Core Loop

Import and order two or three real short clips → establish a wardrobe reference for one subject → analyse later frames → inspect timestamped A/B evidence → mark a discrepancy as an error or declare an intentional reference change → recompute comparisons using the appropriate reference → export findings for editing.

One wardrobe reference is active at a given sequence position. Earlier versions are preserved. Reference applicability follows the creator's sequence order and chosen frame, not recording timestamps.

## Inspiration & Identity

Use the supplied visual reference at `references/continuity-detective-visual-reference.html`: white/off-white surfaces, charcoal typography, thin dividers, square controls, restrained red annotations, a shot list, large A/B evidence frames, a timeline, and a findings panel.

Its hard-coded percentages, detections, sharing controls, and regeneration actions are illustrative only and must not enter the working product as claimed capabilities.

## Why This Matters to the Learner

Explore “distinguishing intentional narrative shifts from accidental continuity drift.” This experiment grounds intent in explicit creator declarations, with computed evidence supporting review. It does not assume the system can infer unobserved causal events or narrative intent on its own.

## What “Working” Looks Like

Demonstrate the following in approximately one minute using two or three real short clips of the same person:

1. Load the ordered sequence. Automatically propose a clear early reference frame and torso crop, show the reference, and display keyframe comparisons with a computed difference score.
2. Detect a clear unwanted wardrobe difference, with a timestamp, actual reference/comparison frames, and a label supported by the analysis. Clicking the finding seeks both evidence players to their recorded source positions.
3. Declare “New wardrobe from here” at an intentional change. Show the old reference's earlier scope and the new reference's forward scope.
4. Recompute. The intentional change is accepted or no longer unresolved, while a second unwanted drift after it remains flagged against the updated reference. Earlier frames retain their original reference association.
5. Export findings an editor can use, including evidence locations and human review decisions.

No fake overlays or canned findings. A score represents a documented computed difference, not an invented confidence percentage. Do not claim a garment name, material, missing layer, or colour unless the implemented analysis supports it. Automatic reference selection and torso cropping are requested behavior whose feasible method and limitations must be resolved in the technical plan.

## The POC Boundary

- A single subject and one active wardrobe reference at each point in an ordered short sequence.
- Clip import and ordering, reference establishment, wardrobe comparison, timestamped A/B evidence, navigation, human review, explicit forward reference changes, and findings export form one complete workflow.
- Include explicit “not assessable” outcomes for occluded, blurred, or ambiguous regions. Such outcomes must not be presented as continuity matches or errors.
- Actual computed evidence supports every finding. Preserve source timestamps, relevant reference versions, and creator decisions so results can be interpreted and checked.
- Validate with real footage that includes an unchanged wardrobe, a visible wardrobe difference, an intentional reference change, a subsequent unwanted difference, and unusable visual evidence.
- Requested architecture constraints: React + TypeScript + Vite frontend, Python + FastAPI backend, and a separate analysis worker. Implementation details belong in the spec.
- The curriculum targets 2–4 hours of active work, a short demo video, and a public GitHub repository. Deployment is optional. Technical planning must assess whether the complete requested workflow fits that time; scope approval is not evidence that the analysis already works.

## Later

- Prop and face checks, each added only after independent validation.
- Script/slate metadata and scene/story-day continuity blocks.
- Nonlinear story graphs and propagation between branches or takes.
- Separate garment-layer state and additive/subtractive transitions.
- Progressive damage masks and accumulation rules.
- Broader semantic reasoning about causal events and cumulative narrative contradictions.

## Explicitly Cut

- Automatic repair, prompt regeneration, and regeneration shortcuts: version one ends with review and export.
- Sharing controls copied from the design example: outside the requested core inspection workflow.
- Lighting, eyeline, and other detection categories shown in the mockup: not validated wardrobe capabilities.
- Fabricated detections, fixed scores, and unsupported confidence claims: incompatible with evidence-backed inspection.

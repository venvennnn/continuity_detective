---
doc: initial-brief
status: captured
---

# Continuity Detective — User Brief

Continuity Detective replaces the earlier ContagionCut direction. This records the user's instructions, not an approved scope, PRD, or specification.

A video inspection workbench for creators assembling AI-generated shots.

## Workflow

Import ordered clips, establish references and subjects, analyse continuity, show timestamped evidence, support human review, and export findings.

Start with a complete wardrobe/reference-consistency workflow. Add prop and face checks later as independently validated capabilities.

Findings must link to actual computed evidence. Include explicit “not assessable” states for occluded, blurred, or ambiguous regions. No automatic repair or regeneration in the first version.

## Requested Architecture

- Frontend: React + TypeScript + Vite.
- Backend: Python + FastAPI.
- Separate analysis worker.

## Visual Reference

Saved at `references/continuity-detective-visual-reference.html`.

Use white/off-white surfaces, charcoal typography, thin dividers, square controls, restrained red annotations, a shot list, large A/B evidence frames, a timeline, and a findings panel.

The supplied HTML is a design example only. Its percentages, detections, regeneration actions, and sharing controls are not product requirements or evidence of working capabilities. Do not carry its hard-coded metrics or findings into the working product.

## Process

Follow the installed Devpost Learn stages. Preserve planning documents in `devpost/`. Onboarding is in progress; no scope, PRD, specification, or build checklist has been approved yet.

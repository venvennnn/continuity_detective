export type Crop = [number, number, number, number]
export interface Evidence {
  id: string; asset_id: string; clip_id: string; source_hash: string;
  ordinal: number; pts: number; time_base: string; time_ms: number;
  width: number; height: number; crop: Crop; crop_origin: string;
  effective_polygon?: number[][] | null; effective_mask_hash?: string;
  quality_reasons: string[]; quality: Record<string, number>;
  image_hash: string; model_hash: string;
}
export interface Clip {
  id: string; filename: string; source_hash: string; size: number; media_url?: string;
  metadata: { duration_ms: number; width: number; height: number; rotation: number;
    frames: { ordinal: number; time_ms: number; pts: number }[] };
  samples: Evidence[]; proposal_id: string | null;
}
export interface Reference {
  id: string; confirmed: true; evidence_id: string; crop: Crop;
  start_clip_id: string; start_ms: number;
}
export type Decision = 'needs_fix' | 'intentional' | 'false_positive' | 'defer'
export interface Review {
  decision?: Decision; assessment?: 'occluded' | 'blurred' | 'ambiguous'; updated_at: string;
}
export interface Finding {
  id: string; fingerprint: string; reference_id: string;
  reference_evidence: Evidence; candidate_evidence: Evidence;
  status: 'difference' | 'no_difference_flagged' | 'not_assessable';
  score: number | null; threshold: number; reasons: string[]; description: string;
  raw_distance: number | null; decision: Decision | null;
}
export interface Analysis {
  results: Finding[]; references: Reference[]; algorithm: string;
  coverage: { sample_interval_ms: number; samples: number; note: string };
  config: Record<string, unknown>; validation_status: string;
}
export interface Sequence {
  id: string; url: string; duration_ms: number;
  segments: { clip_id: string; offset_ms: number; duration_ms: number }[];
}
export interface Job<T = unknown> {
  id: string; state: string; phase: string; completed: number; total: number;
  result?: T; error?: string | null;
}
export interface ReferenceEvent {
  id: string; type: 'create' | 'correct' | 'undo'; timestamp: string;
  references: Reference[]; previous_references: Reference[]; originating_finding?: string;
}
export interface Project {
  id: string; revision: number; name: string; clips: Clip[]; references: Reference[];
  events: ReferenceEvent[]; analysis: Analysis | null; history: Finding[];
  reviews: Record<string, Review>; sequence: Sequence | null;
  analysedRevision: number | null;
  undo: { references: Reference[]; analysis: Analysis | null; reviews: Record<string, Review>;
    analysedRevision: number | null }[];
}
export const assetUrl = (id: string) => `/api/assets/${id}`
export const mediaUrl = (id: string) => `/api/media/${id}`
export function timecode(ms: number) {
  const total = Math.max(0, ms); const minutes = Math.floor(total / 60000)
  return `${String(minutes).padStart(2, '0')}:${String(Math.floor(total / 1000) % 60).padStart(2, '0')}.${String(Math.floor(total % 1000)).padStart(3, '0')}`
}
export function sequenceTime(p: Project, clipId: string, ms: number) {
  let offset = 0
  for (const clip of p.clips) { if (clip.id === clipId) return offset + ms; offset += clip.metadata.duration_ms }
  return ms
}
export function effectiveStatus(f: Finding, review?: Review) {
  return review?.assessment ? 'not_assessable' : f.status
}

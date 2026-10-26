import type { Analysis, Clip, Project, Reference, Review, Sequence } from './types'

export const emptyProject = (): Project => ({
  id: crypto.randomUUID(), revision: 0, name: 'Untitled sequence', clips: [], references: [],
  events: [], analysis: null, history: [], reviews: {}, sequence: null, analysedRevision: null, undo: [],
})
type Action = { type: 'restore'; project: Project } | { type: 'clips'; clips: Clip[]; name?: string }
  | { type: 'sequence'; sequence: Sequence; revision: number }
  | { type: 'reference'; reference: Reference; replace?: boolean; originating?: string }
  | { type: 'results'; analysis: Analysis; revision: number }
  | { type: 'review'; id: string; review: Review } | { type: 'undo' }
export function projectReducer(p: Project, action: Action): Project {
  switch (action.type) {
    case 'restore': return action.project
    case 'clips': return { ...p, clips: action.clips, name: action.name || p.name,
      revision: p.revision + 1, sequence: null }
    case 'sequence': return p.revision === action.revision ? { ...p, sequence: action.sequence } : p
    case 'reference': {
      const references = action.replace ? [...p.references.slice(0, -1), action.reference] : [...p.references, action.reference]
      return { ...p, revision: p.revision + 1, references,
        undo: [...p.undo, { references: p.references, analysis: p.analysis, reviews: p.reviews, analysedRevision: p.analysedRevision }],
        events: [...p.events, { id: crypto.randomUUID(), type: action.replace ? 'correct' : 'create',
          timestamp: new Date().toISOString(), references, previous_references: p.references, originating_finding: action.originating }] }
    }
    case 'results': {
      if (p.revision !== action.revision) return p
      const ids = new Set(action.analysis.results.map(f => f.fingerprint))
      const history = new Map(p.history.map(f => [f.id, f]))
      p.analysis?.results.filter(f => !ids.has(f.fingerprint)).forEach(f => history.set(f.id, f))
      return { ...p, analysis: action.analysis, analysedRevision: p.revision, history: [...history.values()] }
    }
    case 'review': return { ...p, reviews: { ...p.reviews, [action.id]: action.review } }
    case 'undo': {
      const last = p.undo.at(-1)
      if (!last) return p
      const revision = p.revision + 1
      const restored = new Set(last.analysis?.results.map(f => f.id) || [])
      const historical = new Map(p.history.map(f => [f.id, f]))
      p.analysis?.results.filter(f => !restored.has(f.id)).forEach(f => historical.set(f.id, f))
      return { ...p, revision, references: last.references, analysis: last.analysis,
        reviews: { ...p.reviews, ...last.reviews }, history: [...historical.values()],
        analysedRevision: last.analysis ? revision : null, undo: p.undo.slice(0, -1),
        events: [...p.events, { id: crypto.randomUUID(), type: 'undo', timestamp: new Date().toISOString(),
          references: last.references, previous_references: p.references }] }
    }
  }
}

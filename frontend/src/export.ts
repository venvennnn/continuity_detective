import { assetUrl, effectiveStatus, type Project } from './types'
import { loadImage, saveImage } from './persistence'

async function dataUrl(id: string) {
  let blob = await loadImage(id)
  if (!blob) {
    const response = await fetch(assetUrl(id))
    if (!response.ok) throw new Error('Evidence image unavailable. Reconnect source media before exporting.')
    blob = await response.blob(); await saveImage(id, blob)
  }
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader(); reader.onload = () => resolve(reader.result as string)
    reader.onerror = () => reject(reader.error); reader.readAsDataURL(blob)
  })
}
export async function exportProject(p: Project) {
  if (p.analysedRevision !== p.revision) throw new Error('Re-run analysis before exporting current findings.')
  const current = new Set(p.analysis?.results.map(f => f.id) || [])
  const all = new Map([...p.history, ...(p.analysis?.results || [])].map(f => [f.id, f]))
  const imageCache = new Map<string, string>()
  for (const f of all.values()) for (const e of [f.reference_evidence, f.candidate_evidence]) {
    if (!imageCache.has(e.id)) imageCache.set(e.id, await dataUrl(e.id))
  }
  const output = {
    schema_version: 1, project_id: p.id, name: p.name, exported_at: new Date().toISOString(),
    clips: p.clips.map(({ id, filename, source_hash, metadata }) => ({ id, filename, source_hash,
      duration_ms: metadata.duration_ms })),
    analysis: p.analysis && { algorithm: p.analysis.algorithm, config: p.analysis.config,
      coverage: p.analysis.coverage, validation_status: p.analysis.validation_status },
    references: p.references, reference_events: p.events,
    findings: [...all.values()].map(f => ({ ...f, automatic_status: f.status,
      effective_status: effectiveStatus(f, p.reviews[f.id]), human_review: p.reviews[f.id] || null,
      effective_severity: p.reviews[f.id]?.assessment ? null : f.score,
      superseded: !current.has(f.id), reference_evidence: { ...f.reference_evidence, thumbnail: imageCache.get(f.reference_evidence.id) },
      candidate_evidence: { ...f.candidate_evidence, thumbnail: imageCache.get(f.candidate_evidence.id) } })),
  }
  const url = URL.createObjectURL(new Blob([JSON.stringify(output, null, 2)], { type: 'application/json' }))
  const anchor = document.createElement('a'); anchor.href = url; anchor.download = 'continuity-findings.json'; anchor.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

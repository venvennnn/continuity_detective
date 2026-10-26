import { useRef, useState } from 'react'
import type { PointerEvent } from 'react'
import { assetUrl, timecode, type Clip, type Crop, type Evidence } from '../types'
import EvidenceImage from './EvidenceImage'

export default function ReferenceEditor({ clips, initial, mode, initialCrop, onClose, onConfirm, onExtract }: {
  clips: Clip[]; initial: Evidence; initialCrop?: Crop; mode: 'initial' | 'new' | 'correct';
  onClose: () => void; onConfirm: (e: Evidence, crop: Crop) => void;
  onExtract: (clipId: string, ms: number) => Promise<Evidence>
}) {
  const [evidence, setEvidence] = useState(initial)
  const [crop, setCrop] = useState<Crop>(initialCrop || initial.crop.map(v => Math.min(1, Math.max(0, v))) as Crop)
  const [clipId, setClipId] = useState(initial.clip_id)
  const [time, setTime] = useState(initial.time_ms)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const svgRef = useRef<SVGSVGElement>(null)
  const drag = useRef<{ kind: string; x: number; y: number; crop: Crop } | null>(null)
  const clip = clips.find(c => c.id === clipId) || clips[0]
  const select = (e: Evidence) => {
    setEvidence(e); setClipId(e.clip_id); setTime(e.time_ms)
    const [x, y, w, h] = e.crop
    const a = Math.max(0, Math.min(0.96, x)), b = Math.max(0, Math.min(0.96, y))
    setCrop([a, b, Math.max(0.02, Math.min(w, 1-a)), Math.max(0.02, Math.min(h, 1-b))])
  }
  function start(event: PointerEvent<SVGElement>, kind: string) {
    event.preventDefault(); event.currentTarget.setPointerCapture(event.pointerId)
    drag.current = { kind, x: event.clientX, y: event.clientY, crop: [...crop] }
  }
  function move(event: PointerEvent<SVGSVGElement>) {
    if (!drag.current || !svgRef.current) return
    const bounds = svgRef.current.getBoundingClientRect(); const d = drag.current
    const dx = (event.clientX - d.x) / bounds.width, dy = (event.clientY - d.y) / bounds.height
    const [x, y, w, h] = d.crop; const clamp = (n: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, n))
    if (d.kind === 'move') setCrop([clamp(x+dx, 0, 1-w), clamp(y+dy, 0, 1-h), w, h])
    else {
      const left = d.kind.includes('w') ? clamp(x+dx, 0, x+w-0.02) : x
      const top = d.kind.includes('n') ? clamp(y+dy, 0, y+h-0.02) : y
      const right = d.kind.includes('e') ? clamp(x+w+dx, left+0.02, 1) : x+w
      const bottom = d.kind.includes('s') ? clamp(y+h+dy, top+0.02, 1) : y+h
      setCrop([left, top, right-left, bottom-top])
    }
  }
  async function extract() {
    setLoading(true); setError('')
    try { select(await onExtract(clipId, time)) } catch (e) { setError(String(e)) } finally { setLoading(false) }
  }
  const valid = crop[0] >= 0 && crop[1] >= 0 && crop[2] > 0 && crop[3] > 0 && crop[0]+crop[2] <= 1.001 && crop[1]+crop[3] <= 1.001
  return <div className="modal-shade" onKeyDown={e => { if (e.key === 'Escape') onClose() }}>
    <section className="reference-modal" role="dialog" aria-modal="true" aria-labelledby="reference-title">
      <header className="modal-header"><div><span className="eyebrow">Reference / {mode === 'initial' ? 'Establish' : 'Update'}</span>
        <h2 id="reference-title">{mode === 'initial' ? 'Establish the wardrobe reference.' : 'New wardrobe from here.'}</h2></div>
        <button className="icon-button" onClick={onClose} aria-label="Close reference editor">×</button></header>
      <div className="modal-content">
        <div className="crop-stage" style={{ aspectRatio: `${evidence.width}/${evidence.height}` }}>
          <EvidenceImage evidence={evidence} />
          <svg ref={svgRef} viewBox="0 0 100 100" preserveAspectRatio="none" onPointerMove={move}
            onPointerUp={() => { drag.current = null }} onPointerCancel={() => { drag.current = null }}>
            <rect className="crop-rectangle" x={crop[0]*100} y={crop[1]*100} width={crop[2]*100} height={crop[3]*100}
              onPointerDown={e => start(e, 'move')} />
            {(['nw', 'ne', 'sw', 'se'] as const).map(kind => <rect key={kind} className="crop-handle"
              x={(crop[0] + (kind.includes('e') ? crop[2] : 0))*100-0.7}
              y={(crop[1] + (kind.includes('s') ? crop[3] : 0))*100-0.7} width="1.4" height="1.4"
              onPointerDown={e => start(e, kind)} />)}
          </svg>
        </div>
        <div className="editor-aside"><span className="eyebrow">Creator confirmation</span>
          <p>{mode === 'initial' ? 'Choose a clear view of the clothing you want to track. Nothing is compared until you confirm.' : 'Set as new wardrobe reference from this frame onward? Earlier frames keep their previous reference.'}</p>
          <p className="mono">{clips.find(c => c.id === evidence.clip_id)?.filename}<br />{timecode(evidence.time_ms)} · Frame {evidence.ordinal}</p>
          <p className="quality-note">{evidence.crop_origin === 'manual_selection_aid' ? 'No clear person found. This rectangle is a manual selection aid.' : 'Upper-torso proposal. Drag the rectangle or its corners to adjust.'}</p>
          {evidence.quality_reasons.length > 0 && <p className="warning">Quality check: {evidence.quality_reasons.join(', ').replaceAll('_', ' ')}. Confirmation does not override assessment limits.</p>}
          <div className="crop-fields">{['X', 'Y', 'Width', 'Height'].map((label, i) => <label key={label}>{label}<input type="number" min="0" max="1" step="0.01" aria-label={`Crop ${label}`} value={Number(crop[i].toFixed(3))}
            onChange={event => setCrop(c => c.map((v, j) => i === j ? Number(event.target.value) : v) as Crop)} /></label>)}</div>
          <button className="text-button" onClick={() => select(evidence)}>Reset crop</button>
        </div>
      </div>
      <div className="reference-filmstrip">{clips.map(c => <div key={c.id}><span className="mono small">{c.filename}</span><div className="filmstrip-row">
        {c.samples.map(e => <button key={e.id} className={`film-frame ${e.id === evidence.id ? 'selected' : ''}`} onClick={() => select(e)} aria-label={`Select ${c.filename} at ${timecode(e.time_ms)}`}>
          <img src={assetUrl(e.id)} alt="" /><span>{timecode(e.time_ms)}</span></button>)}
      </div></div>)}</div>
      <div className="exact-selection"><label>Any source frame <select value={clipId} onChange={e => { setClipId(e.target.value); setTime(0) }}>{clips.map(c => <option key={c.id} value={c.id}>{c.filename}</option>)}</select></label>
        <input aria-label="Exact frame time in seconds" type="number" min="0" max={clip.metadata.duration_ms/1000} step="0.001" value={time/1000} onChange={e => setTime(Number(e.target.value)*1000)} />
        <span className="muted small">seconds</span><button onClick={extract} disabled={loading}>{loading ? 'Extracting…' : 'Load exact frame'}</button></div>
      {error && <p className="error">{error}</p>}
      <footer className="modal-footer"><span className="muted small">{mode === 'initial' ? 'Reference applies from the sequence start.' : `Starts at ${timecode(evidence.time_ms)} in this clip.`}</span>
        <div><button onClick={onClose}>Cancel</button><button className="primary" disabled={!valid || loading} onClick={() => onConfirm(evidence, crop)}>{mode === 'initial' ? 'Use this reference' : 'Confirm new reference'}</button></div></footer>
    </section>
  </div>
}

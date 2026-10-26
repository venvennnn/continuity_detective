import { useEffect, useRef } from 'react'
import { mediaUrl, timecode, type Clip, type Evidence } from '../types'
import EvidenceImage from './EvidenceImage'

export default function EvidencePlayer({ label, evidence, clip, danger = false }: {
  label: string; evidence: Evidence; clip?: Clip; danger?: boolean
}) {
  const ref = useRef<HTMLVideoElement>(null)
  useEffect(() => {
    const video = ref.current; if (!video) return
    const seek = () => { video.currentTime = evidence.time_ms / 1000 }
    if (video.readyState >= 1) seek(); else video.addEventListener('loadedmetadata', seek, { once: true })
    return () => video.removeEventListener('loadedmetadata', seek)
  }, [evidence.id, evidence.time_ms])
  return <div className={`evidence-card ${danger ? 'danger' : ''}`}>
    <div className="evidence-label"><span>{label} / {clip?.filename || evidence.clip_id}</span><span>{timecode(evidence.time_ms)}</span></div>
    <EvidenceImage evidence={evidence} overlay />
    <div className="evidence-caption"><span>FRAME {evidence.ordinal}</span><span>Exact analysed pixels</span></div>
    <details><summary>Source playback</summary><video ref={ref} src={mediaUrl(evidence.clip_id)} controls preload="metadata" /></details>
  </div>
}

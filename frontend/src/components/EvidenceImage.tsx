import { useEffect, useState } from 'react'
import { assetUrl, type Evidence } from '../types'
import { loadImage, saveImage } from '../persistence'

export default function EvidenceImage({ evidence, overlay = false, className = '' }: {
  evidence: Evidence; overlay?: boolean; className?: string
}) {
  const [cached, setCached] = useState<{id:string;url:string}|null>(null)
  const src = cached?.id === evidence.id ? cached.url : assetUrl(evidence.id)
  useEffect(() => {
    let active = true; let objectUrl: string | undefined
    fetch(assetUrl(evidence.id)).then(async response => {
      if (!response.ok) throw new Error('Offline')
      const blob = await response.blob(); await saveImage(evidence.id, blob)
    }).catch(async () => {
      const blob = await loadImage(evidence.id).catch(() => null)
      if (blob && active) { objectUrl = URL.createObjectURL(blob); setCached({id:evidence.id,url:objectUrl}) }
    })
    return () => { active = false; if (objectUrl) URL.revokeObjectURL(objectUrl) }
  }, [evidence.id])
  const points = evidence.effective_polygon || [
    [evidence.crop[0], evidence.crop[1]], [evidence.crop[0] + evidence.crop[2], evidence.crop[1]],
    [evidence.crop[0] + evidence.crop[2], evidence.crop[1] + evidence.crop[3]], [evidence.crop[0], evidence.crop[1] + evidence.crop[3]],
  ]
  return <div className={`evidence-image ${className}`} style={{ aspectRatio: `${evidence.width}/${evidence.height}` }}>
    <img src={src} alt={`Evidence from ${evidence.clip_id}, frame ${evidence.ordinal}`} />
    {overlay && <svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-label="Analysed clothing region">
      <polygon points={points.map(([x, y]) => `${x * 100},${y * 100}`).join(' ')} />
    </svg>}
  </div>
}

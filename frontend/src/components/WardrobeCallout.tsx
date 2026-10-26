import { useEffect,useState } from 'react'
import { measureColour,type ColourEvidence } from '../colourEvidence'
import type { Evidence,Finding } from '../types'

export default function WardrobeCallout({finding,previous,previousName,currentName,referenceName}:{
  finding:Finding;previous?:Evidence;previousName:string;currentName:string;referenceName:string
}) {
  const [loaded,setLoaded]=useState<{key:string;before:ColourEvidence;after:ColourEvidence;baseline:ColourEvidence}|null>(null)
  const acrossCut=!!previous && !previous.quality_reasons.length
  const beforeEvidence=acrossCut ? previous! : finding.reference_evidence
  const key=`${beforeEvidence.id}/${finding.id}`
  useEffect(()=>{
    let active=true
    Promise.all([measureColour(beforeEvidence),measureColour(finding.candidate_evidence),measureColour(finding.reference_evidence)])
      .then(([before,after,baseline])=>{if(active)setLoaded({key,before,after,baseline})}).catch(()=>{})
    return()=>{active=false}
  },[key,beforeEvidence,finding])
  const colours=loaded?.key===key?loaded:null
  return <div className="wardrobe-callout" role="status" aria-label="Wardrobe colour change">
    <div className="wardrobe-alert-title"><span className="wardrobe-alert-icon">!</span><span>WARDROBE CHANGE DETECTED</span></div>
    {colours?<>
      <div className="colour-transition"><span><i style={{background:colours.before.swatch}}/>{colours.before.name}</span><b>→</b><span><i style={{background:colours.after.swatch}}/>{colours.after.name}</span></div>
      <div className="colour-proof"><div><img src={colours.before.thumbnail} alt={`Previous clothing crop, ${colours.before.name}`}/><span>BEFORE</span></div><span className="proof-arrow">→</span><div><img src={colours.after.thumbnail} alt={`Current clothing crop, ${colours.after.name}`}/><span>NOW</span></div><p>Clothing colour changed.<br/><span>{colours.before.name===colours.after.name?'Appearance differs within the same broad colour.':'Review this continuity difference.'}</span></p></div>
      <div className="colour-source">{acrossCut?'Across cut':'Reference comparison'} · {acrossCut?previousName:referenceName} → {currentName}<br/>Active reference: {colours.baseline.name} · Estimated crop colours</div>
    </>:<><div className="colour-transition">Clothing appearance changed</div><div className="colour-source">Inspect the highlighted region against the reference.</div></>}
  </div>
}

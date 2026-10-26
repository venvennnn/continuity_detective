import { useEffect, useMemo, useReducer, useRef, useState } from 'react'
import { post, request, waitJob } from './api'
import { emptyProject, projectReducer } from './projectReducer'
import { loadProject, saveProject, saveImage } from './persistence'
import { exportProject } from './export'
import { assetUrl, effectiveStatus, sequenceTime, timecode } from './types'
import type { Analysis, Clip, Crop, Evidence, Finding, Job, Reference, Review, Sequence } from './types'
import ReferenceEditor from './components/ReferenceEditor'
import EvidencePlayer from './components/EvidencePlayer'
import EvidenceImage from './components/EvidenceImage'
import WardrobeCallout from './components/WardrobeCallout'
import { MagneticButton } from './motion'
import { usePointerGlow } from './usePointerGlow'
import './App.css'

const TICKER = ['Inspect', 'Compare', 'Decide', 'Local only', 'Wardrobe continuity', 'Evidence first', 'Creator review']

export default function App() {
  const [p, dispatch] = useReducer(projectReducer, undefined, emptyProject)
  const projectRef = useRef(p)
  useEffect(() => { projectRef.current = p }, [p])
  const [ready, setReady] = useState(false)
  const [busy, setBusy] = useState<{ label: string; completed?: number; total?: number } | null>(null)
  const [error, setError] = useState(''), [notice, setNotice] = useState('')
  const [savedSnapshot, setSavedSnapshot] = useState<typeof p | null>(null)
  const [saveError, setSaveError] = useState(false)
  const saveState = saveError ? 'Not saved — storage unavailable' : savedSnapshot === p ? 'Saved locally' : 'Saving…'
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [selectedFrame, setSelectedFrame] = useState<Evidence | null>(null)
  const [editor, setEditor] = useState<{ evidence: Evidence; mode: 'initial' | 'new' | 'correct'; crop?: Crop } | null>(null)
  const [tab, setTab] = useState<'sequence' | 'evidence'>('sequence')
  const [filter, setFilter] = useState<'findings' | 'all' | 'history'>('findings')
  const [playTime, setPlayTime] = useState(0), [playing, setPlaying] = useState(false)
  const [missing, setMissing] = useState<string[]>([]), [workerOnline, setWorkerOnline] = useState(false)
  const [pauseOnFinding, setPauseOnFinding] = useState(false)
  const player = useRef<HTMLVideoElement>(null), fileInput = useRef<HTMLInputElement>(null)
  const pausedShots = useRef(new Set<string>())
  const glow = usePointerGlow()
  const current = !!p.analysis && p.analysedRevision === p.revision
  const results = useMemo(() => p.analysis?.results || [], [p.analysis])
  const selected = results.find(f => f.id === selectedId) || results.find(f => f.status === 'difference') || results[0]
  const activeEvidence = selectedFrame || selected?.candidate_evidence || p.clips[0]?.samples[0]
  const referenceEvidence = selected?.reference_evidence || p.clips.flatMap(c => c.samples).find(e => e.id === p.references.at(-1)?.evidence_id)
  const totalMs = p.clips.reduce((n, c) => n + c.metadata.duration_ms, 0)
  const differences = results.filter(f => effectiveStatus(f, p.reviews[f.id]) === 'difference' &&
    !['intentional','false_positive'].includes(p.reviews[f.id]?.decision || ''))
  const assessmentCount = results.filter(f => effectiveStatus(f, p.reviews[f.id]) === 'not_assessable').length
  const shotsFlagged = new Set(differences.map(f => f.candidate_evidence.clip_id)).size
  const firstReference = p.clips.flatMap(c => c.samples).find(e => e.id === p.references[0]?.evidence_id)
  const candidate = p.clips.flatMap(c => c.samples).find(e => !e.quality_reasons.length) || p.clips[0]?.samples[0]
  const name = (id: string) => p.clips.find(c => c.id === id)?.filename || id
  const progress = (job: Job) => setBusy({ label: job.phase || 'Waiting for worker', completed: job.completed, total: job.total })

  async function makeSequence(clips: Clip[], revision: number) {
    const queued = await post<{ job_id: string }>('/sequences', { clip_ids: clips.map(c => c.id) })
    const sequence = await waitJob<Sequence>(queued.job_id, progress)
    dispatch({ type: 'sequence', sequence, revision })
  }
  async function loadDemo() {
    setError(''); setBusy({ label: 'Opening your supplied takes' })
    try {
      const demo = await request<{ clips: Clip[]; jobs: { clip_id: string; job_id: string }[] }>('/demo')
      const prepared = demo.clips.filter(c => c.samples?.length)
      for (const job of demo.jobs) prepared.push(await waitJob<Clip>(job.job_id, progress))
      prepared.sort((a, b) => a.filename.localeCompare(b.filename, undefined, { numeric: true }))
      if (!prepared.length) throw new Error('No supplied takes found. Import local clips to begin.')
      dispatch({ type: 'restore', project: { ...emptyProject(), clips: prepared, revision: 1, name: 'The café sequence' } })
      setSelectedFrame(prepared[0].samples[0]); setSelectedId(null); setPlayTime(0); setMissing([]); pausedShots.current.clear()
      await makeSequence(prepared, 1)
    } catch (e) { setError((e as Error).message) } finally { setBusy(null) }
  }
  useEffect(() => {
    let active = true
    void (async () => {
      try {
        const saved = await loadProject(); if (!active) return
        setReady(true)
        if (saved?.clips.length) {
          dispatch({ type: 'restore', project: saved })
          const absent = await Promise.all(saved.clips.map(async c => {
            try { const data = await request<{ available: boolean }>(`/clips/${c.id}`); return data.available ? null : c.id }
            catch { return c.id }
          }))
          if (active) setMissing(absent.filter((id): id is string => !!id))
        } else await loadDemo()
      } catch { if (active) { setReady(true); await loadDemo() } }
    })()
    return () => { active = false }
  }, [])
  useEffect(() => {
    if (!ready) return
    let active = true
    const timer = setTimeout(() => { saveProject(p).then(() => { if(active){setSavedSnapshot(p);setSaveError(false)} }).catch(() => { if(active)setSaveError(true) }) }, 100)
    return () => { active = false; clearTimeout(timer) }
  }, [p, ready])
  useEffect(() => {
    let active = true
    const check = () => request<{ worker: { online: boolean } }>('/health').then(h => { if (active) setWorkerOnline(h.worker.online) }).catch(() => { if (active) setWorkerOnline(false) })
    void check(); const timer = setInterval(check, 5000)
    return () => { active = false; clearInterval(timer) }
  }, [])
  async function runAnalysis(snapshot = projectRef.current) {
    if (!snapshot.references.length) { if (candidate) setEditor({ evidence: candidate, mode: 'initial' }); return }
    if (missing.length) { setError('Relink missing source clips before re-analysis.'); return }
    setError(''); setBusy({ label: 'Computing wardrobe comparisons' })
    try {
      const job = await post<{ job_id: string }>('/analysis-runs', { project_id: snapshot.id, revision: snapshot.revision,
        clip_ids: snapshot.clips.map(c => c.id), references: snapshot.references })
      const analysis = await waitJob<Analysis>(job.job_id, progress)
      setBusy({ label: 'Saving evidence previews locally' })
      const ids = [...new Set(analysis.results.flatMap(f => [f.reference_evidence.id, f.candidate_evidence.id]))]
      try {
        for (let i = 0; i < ids.length; i += 6) await Promise.all(ids.slice(i,i+6).map(async id => {
          const response = await fetch(assetUrl(id)); if (!response.ok) throw new Error('Image unavailable')
          await saveImage(id, await response.blob())
        }))
      } catch { setError('Analysis completed, but some previews could not be saved locally. Keep the backend available or export your evidence.') }
      dispatch({ type: 'results', analysis, revision: snapshot.revision })
      if (projectRef.current.revision === snapshot.revision) {
        setSelectedId((analysis.results.find(f => f.status === 'difference') || analysis.results[0])?.id || null)
        setSelectedFrame(null); setNotice(`${analysis.coverage.samples} frames compared against your confirmed references.`)
      }
    } catch (e) { setError((e as Error).message) } finally { setBusy(null) }
  }
  function commitReference(evidence: Evidence, crop: Crop) {
    const mode = editor?.mode || 'initial', old = projectRef.current
    const preceding = mode === 'correct' ? old.references.at(-2) : old.references.at(-1)
    if (mode !== 'initial' && preceding && sequenceTime(old,evidence.clip_id,evidence.time_ms) <= sequenceTime(old,preceding.start_clip_id,preceding.start_ms)) {
      setError('Choose a frame after the preceding reference boundary. Use Edit reference to correct the current reference.'); return
    }
    const initialScope = mode === 'initial' || (mode === 'correct' && old.references.length === 1)
    const reference: Reference = { id: crypto.randomUUID(), confirmed: true, evidence_id: evidence.id, crop,
      start_clip_id: initialScope ? old.clips[0].id : evidence.clip_id, start_ms: initialScope ? 0 : evidence.time_ms }
    const clips = old.clips.map(c => c.id === evidence.clip_id && !c.samples.some(s => s.id === evidence.id)
      ? { ...c, samples: [...c.samples,evidence].sort((a,b) => a.time_ms-b.time_ms) } : c)
    const next = projectReducer({ ...old, clips }, { type: 'reference', reference, replace: mode === 'correct',
      originating: selected?.candidate_evidence.id === evidence.id ? selected.id : undefined })
    dispatch({ type: 'restore', project: next }); setEditor(null); pausedShots.current.clear(); void runAnalysis(next)
  }
  async function extract(clipId: string, ms: number) {
    const queued = await post<{ job_id: string }>('/frames', { clip_id: clipId, time_ms: ms })
    return waitJob<Evidence>(queued.job_id)
  }
  async function referenceAtPlayhead() {
    let sourceMs = playTime
    let clip = p.clips.at(-1)
    for (const c of p.clips) { if (sourceMs < c.metadata.duration_ms) { clip = c; break } sourceMs -= c.metadata.duration_ms }
    if (!clip) return
    sourceMs = Math.min(Math.max(0, sourceMs), clip.metadata.duration_ms - 1)
    setBusy({label:'Preparing the selected source frame'})
    try {
      const sample = clip.samples.find(e=>Math.abs(e.time_ms-sourceMs)<1)
      setEditor({mode:p.references.length?'new':'initial',evidence:sample || await extract(clip.id,sourceMs)})
    } catch(e) { setError((e as Error).message) } finally { setBusy(null) }
  }
  function seek(ms: number) {
    const video = player.current
    if (video) { video.pause(); if (video.readyState >= 1) video.currentTime = ms/1000
      else video.addEventListener('loadedmetadata', () => { video.currentTime=ms/1000 }, { once:true }) }
    if (!video) setPlayTime(ms)
  }
  function selectFinding(f: Finding) { setSelectedId(f.id); setSelectedFrame(null); seek(sequenceTime(p,f.candidate_evidence.clip_id,f.candidate_evidence.time_ms)) }
  const liveFinding = useMemo(() => {
    if (!current) return undefined
    const playingClip=p.clips.find(c=>{const start=sequenceTime(p,c.id,0);return playTime>=start && playTime<start+c.metadata.duration_ms})||p.clips.at(-1)
    let best: Finding | undefined, delta=300
    for (const f of results) { if(f.candidate_evidence.clip_id!==playingClip?.id)continue;const d=Math.abs(sequenceTime(p,f.candidate_evidence.clip_id,f.candidate_evidence.time_ms)-playTime); if(d<delta){best=f;delta=d} }
    return best
  }, [current,results,p,playTime])
  const liveReview = liveFinding && p.reviews[liveFinding.id]
  const liveStatus = liveFinding ? effectiveStatus(liveFinding,liveReview) : undefined
  const liveActionable = liveStatus==='difference' && !['intentional','false_positive'].includes(liveReview?.decision || '')
  const liveClipIndex = liveFinding ? p.clips.findIndex(c=>c.id===liveFinding.candidate_evidence.clip_id) : -1
  const previousClip = liveClipIndex>0 ? p.clips[liveClipIndex-1] : undefined
  const onsets = differences.filter((f,i,list)=>!list.slice(0,i).some(g=>g.candidate_evidence.clip_id===f.candidate_evidence.clip_id && g.reference_id===f.reference_id))
  function onTime(ms:number) {
    setPlayTime(ms); if(!pauseOnFinding || !current)return
    const onset=onsets.find(f=>{const t=sequenceTime(p,f.candidate_evidence.clip_id,f.candidate_evidence.time_ms);return ms>=t && ms<t+350 && !pausedShots.current.has(f.id)})
    if(onset){pausedShots.current.add(onset.id);selectFinding(onset);setNotice('Paused at the first flagged sample in this shot.')}
  }
  async function importFiles(files:FileList|null) {
    if(!files?.length)return
    if(files.length>3 || [...files].reduce((n,f)=>n+f.size,0)>250*1024*1024){setError('Import up to three clips, 250 MiB total.');return}
    setError('');setBusy({label:'Importing your sequence'})
    try {
      const clips:Clip[]=[]
      for(const file of files){const form=new FormData();form.append('file',file);form.append('project_id',p.id)
        const queued=await request<{job_id:string}>('/clips',{method:'POST',body:form});clips.push(await waitJob<Clip>(queued.job_id,progress))}
      dispatch({type:'restore',project:{...emptyProject(),revision:1,clips}});setSelectedFrame(clips[0].samples[0]);setSelectedId(null);setMissing([]);setPlayTime(0)
      await makeSequence(clips,1)
      const e=clips.flatMap(c=>c.samples).find(e=>!e.quality_reasons.length)||clips[0].samples[0]
      if(e)setEditor({mode:'initial',evidence:e})
    }catch(e){setError((e as Error).message)}finally{setBusy(null);if(fileInput.current)fileInput.current.value=''}
  }
  async function reorder(index:number,direction:number) {
    const clips=[...p.clips];[clips[index],clips[index+direction]]=[clips[index+direction],clips[index]]
    const next={...p,clips,revision:p.revision+1,references:[],analysis:null,history:[...p.history,...results],analysedRevision:null,sequence:null,undo:[]}
    dispatch({type:'restore',project:next});setNotice('Order changed. Confirm a reference for the new order before re-analysis.');setBusy({label:'Rebuilding sequence order'})
    try{await makeSequence(clips,next.revision)}catch(e){setError((e as Error).message)}finally{setBusy(null)}
  }
  function review(change:Partial<Review>){if(selected)dispatch({type:'review',id:selected.id,review:{...p.reviews[selected.id],...change,updated_at:new Date().toISOString()}})}
  async function download(){setBusy({label:'Packaging evidence and review history'});setError('');try{await exportProject(projectRef.current);setNotice('JSON exported with embedded evidence and reference history.')}catch(e){setError((e as Error).message)}finally{setBusy(null)}}
  async function relink(clip:Clip,file:File){setBusy({label:`Relinking ${clip.filename}`});try{const form=new FormData();form.append('file',file);await request(`/clips/${clip.id}/relink`,{method:'POST',body:form});setMissing(ids=>ids.filter(id=>id!==clip.id))}catch(e){setError((e as Error).message)}finally{setBusy(null)}}
  const groups=useMemo(()=>{
    const source=filter==='history'?p.history:results, map=new Map<string,Finding[]>()
    for(const f of source){const status=effectiveStatus(f,p.reviews[f.id]);if(filter==='findings' && (status==='no_difference_flagged' || ['intentional','false_positive'].includes(p.reviews[f.id]?.decision || '')))continue
      const key=`${f.candidate_evidence.clip_id}/${f.reference_id}/${status}`;map.set(key,[...(map.get(key)||[]),f])}
    return [...map.values()]
  },[filter,p.history,results,p.reviews])

  return <div className="app-shell">
    <div className="pointer-glow" ref={glow} aria-hidden="true" />
    <header className="topbar"><a className="brand" href="#" onClick={e=>{e.preventDefault();setTab('sequence')}}><span className="brand-mark">◎</span> CONTINUITY DETECTIVE</a><span className="header-divider"/><span className="mono header-project">{p.name}</span><div className="topbar-right"><span className="save-status"><i/>{saveState}</span><MagneticButton onClick={()=>{void download()}} disabled={!current||!!busy}>↗ Export findings</MagneticButton></div></header>
    <section className="hero page-title">
      <div className="hero-copy">
        <div className="eyebrow">Inspection studio <span>/</span> Wardrobe continuity</div>
        <h1>
          <span className="hero-mask"><span className="hero-line">Every shot.</span></span>
          <span className="hero-mask"><span className="hero-line">Same story<span>.</span></span></span>
        </h1>
        <p className="hero-lead">Confirm one wardrobe. Watch every cut against it. Footage stays on this computer.</p>
      </div>
      <div className="sequence-facts">
        <div><strong>{String(p.clips.length).padStart(2,'0')}</strong><span>SHOTS</span></div>
        <div><strong>{timecode(totalMs).slice(0,5)}</strong><span>SEQUENCE</span></div>
        <div><strong>{current?p.analysis?.coverage.samples:'—'}</strong><span>FRAMES ASSESSED</span></div>
      </div>
    </section>
    <div className="ticker" aria-hidden="true"><div className="ticker-track">{[0,1].map(copy => <div className="ticker-copy" key={copy}>{TICKER.map(item => <span key={`${copy}-${item}`}>{item}</span>)}</div>)}</div></div>
    {error&&<div className="message error" role="alert"><span>{error}</span><button onClick={()=>setError('')} aria-label="Dismiss error">×</button></div>}
    {!!missing.length&&<div className="message warning">Original media unavailable. Saved evidence and review remain visible.{p.clips.filter(c=>missing.includes(c.id)).map(c=><label className="relink" key={c.id}>Relink {c.filename}<input type="file" accept="video/*" onChange={e=>{if(e.target.files?.[0])void relink(c,e.target.files[0])}}/></label>)}</div>}
    <section className="shots-panel"><div className="section-heading"><h2>Shot sequence <span>({String(p.clips.length).padStart(2,'0')})</span></h2><button className="text-button" onClick={()=>fileInput.current?.click()} disabled={!!busy}>+ Import</button></div><input ref={fileInput} type="file" accept="video/*" multiple hidden onChange={e=>{void importFiles(e.target.files)}}/><p className="panel-description">Ordered clips. One continuous story.</p>
      <div className="shot-list">{p.clips.map((clip,i)=>{const first=clip.samples[0],flagged=current&&differences.some(f=>f.candidate_evidence.clip_id===clip.id);return <article className={`shot-card ${activeEvidence?.clip_id===clip.id?'active':''}`} key={clip.id}><button className="shot-select" onClick={()=>{setSelectedFrame(first);seek(sequenceTime(p,clip.id,0))}}><div className="shot-image">{first&&<EvidenceImage evidence={first}/>}<span className="shot-number">{String(i+1).padStart(2,'0')}</span><span className="shot-duration">{clip.metadata.duration_ms/1000}s</span></div><div className="shot-info"><strong>{clip.filename}</strong><span className={`shot-state ${flagged?'red':''}`}>{flagged?'● Difference flagged':current?'○ Analysed samples':'○ Ready to inspect'}</span></div></button><div className="shot-footer"><span>{timecode(sequenceTime(p,clip.id,0))}</span><div><button aria-label={`Move ${clip.filename} earlier`} disabled={i===0||!!busy} onClick={()=>{void reorder(i,-1)}}>↑</button><button aria-label={`Move ${clip.filename} later`} disabled={i===p.clips.length-1||!!busy} onClick={()=>{void reorder(i,1)}}>↓</button></div></div></article>})}</div>
      {!p.clips.length&&<div className="empty-shots"><span>＋</span><p>Bring your shots into focus.</p><button onClick={()=>fileInput.current?.click()}>Import clips</button></div>}
      <div className="shot-panel-bottom"><button onClick={()=>{void loadDemo()}} disabled={!!busy}>↺ Open supplied takes</button><span className="mono muted">UP TO 3 CLIPS · LOCAL PROCESSING</span></div></section>
    <div className="studio-grid">
      <main className="inspection-panel"><div className="viewer-toolbar"><div className="tabs"><button className={tab==='sequence'?'active':''} onClick={()=>setTab('sequence')}>Sequence playback</button><button className={tab==='evidence'?'active':''} onClick={()=>setTab('evidence')}>Evidence A/B</button></div><span className={`viewer-state ${current&&liveActionable?'red':''}`}><i/>{busy?'PROCESSING':current?liveActionable?'DIFFERENCE FLAGGED':'INSPECTION READY':'AWAITING REFERENCE'}</span></div>
        <div className="viewer-intro"><div><span className="eyebrow">{tab==='sequence'?'The complete sequence':'Side-by-side inspection'}</span><h2>{tab==='sequence'?'See the change in context.':'The evidence, frame for frame.'}</h2></div><span className="mono muted">{tab==='sequence'?'01 → 02 → 03':'REFERENCE / COMPARISON'}</span></div>
        {tab==='sequence'?<div className="sequence-player" data-testid="sequence-player">{p.sequence?<video ref={player} src={p.sequence.url} controls preload="auto" playsInline onTimeUpdate={e=>{if(!e.currentTarget.seeking)onTime(e.currentTarget.currentTime*1000)}} onSeeked={e=>onTime(e.currentTarget.currentTime*1000)} onPlay={()=>setPlaying(true)} onPause={()=>setPlaying(false)}/>:<div className="player-placeholder">{activeEvidence&&<EvidenceImage evidence={activeEvidence}/>}<div className="placeholder-caption">{busy?busy.label:p.clips.length?'Preparing continuous playback':'Import a sequence to begin'}</div></div>}
          {current&&liveFinding&&<><div className={`video-annotation ${liveActionable?'flagged':''}`}><span>{liveStatus==='not_assessable'?'NOT ASSESSABLE':liveActionable?'WARDROBE COLOUR DIFFERENCE':liveReview?.decision==='intentional'?'INTENTIONAL CHANGE':liveReview?.decision==='false_positive'?'FALSE POSITIVE':'NO COLOUR DIFFERENCE FLAGGED'}</span><span>{name(liveFinding.candidate_evidence.clip_id)} · sample {timecode(liveFinding.candidate_evidence.time_ms)}</span></div>{liveActionable&&<WardrobeCallout finding={liveFinding} previous={previousClip?.samples.at(-1)} previousName={previousClip?.filename||name(liveFinding.reference_evidence.clip_id)} currentName={name(liveFinding.candidate_evidence.clip_id)} referenceName={name(liveFinding.reference_evidence.clip_id)}/>}{liveActionable&&liveFinding.candidate_evidence.effective_polygon&&<svg className="video-region" viewBox="0 0 100 100" preserveAspectRatio="none" aria-label="Flagged clothing region"><polygon points={liveFinding.candidate_evidence.effective_polygon.map(([x,y])=>{const ratio=liveFinding.candidate_evidence.width/liveFinding.candidate_evidence.height,target=16/9;return `${(ratio<target?(1-ratio/target)/2+x*ratio/target:x)*100},${(ratio>target?(1-target/ratio)/2+y*target/ratio:y)*100}`}).join(' ')}/></svg>}</>}
        </div>:<div className="ab-grid">{referenceEvidence&&activeEvidence?<><EvidencePlayer label="A · Reference" evidence={referenceEvidence} clip={p.clips.find(c=>c.id===referenceEvidence.clip_id)}/><EvidencePlayer label="B · Comparison" evidence={activeEvidence} clip={p.clips.find(c=>c.id===activeEvidence.clip_id)} danger={selected?.status==='difference'}/></>:<div className="empty-view">Confirm a reference to reveal timestamped A/B evidence.</div>}</div>}
        <div className="playback-meta"><span className="mono">{timecode(playTime)} <span className="muted">/ {timecode(totalMs)}</span></span><button className="text-button playhead-reference" disabled={!p.clips.length||!!busy} onClick={()=>{void referenceAtPlayhead()}}>Set reference at playhead</button><label className="pause-toggle"><input type="checkbox" checked={pauseOnFinding} onChange={e=>setPauseOnFinding(e.target.checked)}/> Pause at flagged shots</label></div>
        <div className="timeline" data-testid="timeline"><div className="timeline-ruler"><span>00:00</span><span>{timecode(totalMs/2).slice(0,5)}</span><span>{timecode(totalMs).slice(0,5)}</span></div><div className="timeline-track">{p.clips.map((clip,i)=><button key={clip.id} style={{width:`${clip.metadata.duration_ms/Math.max(1,totalMs)*100}%`}} onClick={()=>seek(sequenceTime(p,clip.id,0))} aria-label={`Seek ${clip.filename}`}><span>{String(i+1).padStart(2,'0')}</span>{clip.filename}</button>)}{current&&differences.map(f=><button className="finding-marker" key={f.id} style={{left:`${sequenceTime(p,f.candidate_evidence.clip_id,f.candidate_evidence.time_ms)/Math.max(1,totalMs)*100}%`}} onClick={()=>selectFinding(f)} title={`Wardrobe difference at ${timecode(sequenceTime(p,f.candidate_evidence.clip_id,f.candidate_evidence.time_ms))}`} aria-label={`Seek finding at ${timecode(sequenceTime(p,f.candidate_evidence.clip_id,f.candidate_evidence.time_ms))}`}/>)}{p.references.slice(1).map((ref,i)=><span key={ref.id} className="reference-marker" style={{left:`${sequenceTime(p,ref.start_clip_id,ref.start_ms)/Math.max(1,totalMs)*100}%`}}>R{i+2}</span>)}<span className="playhead" style={{left:`${playTime/Math.max(1,totalMs)*100}%`}}/></div><div className="timeline-legend"><span><i className="legend-red"/> Flagged sample</span><span>│ Reference boundary</span><span>Sampled every 0.5s</span></div></div>
        {!p.references.length?<div className="reference-callout"><div className="callout-symbol">A</div><div><h3>One reference. A consistent wardrobe.</h3><p>{p.clips.some(c=>c.proposal_id)?'A clear early frame is ready. Confirm the clothing region to begin.':'Select a frame where the torso is visible, then adjust the crop.'}</p></div><button className="primary" disabled={!candidate||!!busy} onClick={()=>candidate&&setEditor({mode:'initial',evidence:candidate})}>Review reference →</button></div>:<div className="reference-summary"><div className="reference-summary-image">{firstReference&&<EvidenceImage evidence={firstReference}/>}</div><div><span className="eyebrow">Wardrobe reference</span><strong>{p.references.length===1?'Original baseline':`${p.references.length} reference segments`}</strong><span className="muted small">Earlier frames keep their reference.</span></div><div className="reference-actions"><button disabled={!!busy} onClick={()=>{const ref=p.references.at(-1),e=p.clips.flatMap(c=>c.samples).find(s=>s.id===ref?.evidence_id);if(e)setEditor({mode:'correct',evidence:e,crop:ref?.crop})}}>Edit reference</button><button disabled={!p.undo.length||!!busy} onClick={()=>{dispatch({type:'undo'});setNotice('Previous reference configuration and scores restored.');pausedShots.current.clear()}}>Undo change</button></div></div>}
        {p.analysis&&!current&&<div className="stale-message">Reference or sequence changed. Previous results are historical until re-analysis succeeds.<button disabled={!!busy} onClick={()=>{void runAnalysis()}}>Re-run analysis</button></div>}
        {selected&&current&&<section className="review-workspace"><div className="review-heading"><span className="eyebrow">Human review / selected sample</span><span className="mono">{timecode(sequenceTime(p,selected.candidate_evidence.clip_id,selected.candidate_evidence.time_ms))}</span></div><div className="evidence-mini-grid">{[selected.reference_evidence,selected.candidate_evidence].map((e,i)=><button key={`${i}-${e.id}`} onClick={()=>{setSelectedFrame(null);setTab('evidence')}}><EvidenceImage evidence={e} overlay/><span>{i===0?'A · Reference':'B · Compared frame'} / {name(e.clip_id)}</span></button>)}</div><div className="review-controls"><label>Decision<select aria-label="Decision" value={p.reviews[selected.id]?.decision||selected.decision||'defer'} onChange={e=>review({decision:e.target.value as Review['decision']})}><option value="needs_fix">Needs fix</option><option value="intentional">Intentional · keep reference</option><option value="false_positive">False positive</option><option value="defer">Review later</option></select></label><label>Region assessment<select aria-label="Region assessment" value={p.reviews[selected.id]?.assessment||''} onChange={e=>review({assessment:(e.target.value||undefined) as Review['assessment']})}><option value="">Use automatic assessment</option><option value="occluded">Not assessable · occluded</option><option value="blurred">Not assessable · blurred</option><option value="ambiguous">Not assessable · ambiguous</option></select></label><button className="primary" disabled={!!busy} onClick={()=>setEditor({mode:'new',evidence:selected.candidate_evidence})}>New wardrobe from here →</button></div><p className="small muted">Decisions apply to this sample only. Only a confirmed reference change affects later comparisons.</p></section>}
        {busy&&<div className="job-progress" role="status"><span className="spinner"/><span>{busy.label}</span>{!!busy.total&&<><progress value={busy.completed||0} max={busy.total}/><span className="mono">{busy.completed}/{busy.total}</span></>}</div>}{notice&&<div className="notice" role="status">{notice}<button onClick={()=>setNotice('')} aria-label="Dismiss notice">×</button></div>}
        <div className="inspection-footnote"><span>LOCAL INSPECTION · FOOTAGE STAYS ON THIS COMPUTER</span><span className="worker-status"><i className={workerOnline?'online':''}/>{workerOnline?'Worker online':'Worker unavailable'}</span></div>
      </main>
      <aside className="findings-panel"><div className="section-heading"><h2>Findings <span>({current?String(shotsFlagged).padStart(2,'0'):'—'})</span></h2><span className="red-dot"/></div><div className="finding-tabs"><button className={filter==='findings'?'active':''} onClick={()=>setFilter('findings')}>Flagged</button><button className={filter==='all'?'active':''} onClick={()=>setFilter('all')}>All samples</button><button className={filter==='history'?'active':''} onClick={()=>setFilter('history')}>History</button></div>{p.analysis&&<div className="findings-summary"><span>{differences.length} flagged samples</span><span>{assessmentCount} not assessable</span></div>}
        <div className="findings-list">{groups.map((group,index)=>{const lead=group.find(f=>f.id===selected?.id)||group[0],status=effectiveStatus(lead,p.reviews[lead.id]);return <article key={`${lead.candidate_evidence.clip_id}-${lead.reference_id}-${status}`} className={`finding-card ${group.some(f=>f.id===selected?.id)?'selected':''}`}><button className="finding-main" onClick={()=>{if(filter==='history'){setNotice('Historical evidence is retained in export; select a current sample to review.');return}selectFinding(lead)}}><div className="finding-card-top"><span>{String(index+1).padStart(2,'0')} / {status==='difference'?'WARDROBE COLOUR':status==='not_assessable'?'NOT ASSESSABLE':'COLOUR COMPARISON'}</span><span className={status==='difference'?'red':''}>{status==='not_assessable'?'N/A':lead.score?.toFixed(1)}</span></div><div className="finding-card-time"><span>{name(lead.candidate_evidence.clip_id)}</span><span>{timecode(sequenceTime(p,lead.candidate_evidence.clip_id,lead.candidate_evidence.time_ms))}</span></div><p>{status==='not_assessable'?(p.reviews[lead.id]?.assessment||lead.reasons.join(', ')).replaceAll('_',' '):status==='difference'?'Clothing colour appearance differs from the active wardrobe reference.':'No colour difference flagged in the analysed region.'}</p><span className="sample-count">{group.length} sampled frames · {p.reviews[lead.id]?.decision?.replaceAll('_',' ')||(status==='difference'?'needs review':'measured evidence')}</span></button><details><summary>Inspect individual samples</summary><div className="sample-chips">{group.map(f=><button key={f.id} className={f.id===selected?.id?'active':''} onClick={()=>selectFinding(f)}>{timecode(f.candidate_evidence.time_ms).slice(0,8)}</button>)}</div></details></article>})}</div>
        {!groups.length&&<div className="empty-findings"><span className="empty-reticle">⌖</span><h3>{!p.references.length?'Evidence, before assumptions.':current?'No findings in this view.':'Ready when you are.'}</h3><p>{!p.references.length?'Confirm your wardrobe reference. Real differences will appear here, linked to the frames that produced them.':current?'No colour differences flagged among assessed samples. Unanalysed moments may still contain changes.':'Run analysis against your confirmed reference to inspect continuity.'}</p></div>}
        <div className="findings-bottom"><p>Appearance difference is a computed distance, not confidence. Visibility checks are limited; review uncertain regions as not assessable.</p><button className="export-button" disabled={!current||!!busy} onClick={()=>{void download()}}>↗ Export evidence JSON</button><button className="text-button" disabled={!p.references.length||!!busy||!!missing.length} onClick={()=>{void runAnalysis()}}>Re-run analysis</button></div>
      </aside></div>
    <footer className="app-footer"><span>CONTINUITY DETECTIVE</span><span>Observe. Compare. Decide.</span><span>{playing?'PLAYING':'PAUSED'} · WARDROBE / EXPERIMENTAL</span></footer>
    {editor&&<ReferenceEditor clips={p.clips} initial={editor.evidence} initialCrop={editor.crop} mode={editor.mode} onClose={()=>setEditor(null)} onConfirm={commitReference} onExtract={extract}/>}
  </div>
}

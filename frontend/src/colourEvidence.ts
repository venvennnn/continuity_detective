import { assetUrl, type Evidence } from './types'
import { loadImage } from './persistence'

export interface ColourEvidence { name: string; rgb: [number,number,number]; swatch: string; thumbnail: string }
export function colourName([r,g,b]: [number,number,number]) {
  const max=Math.max(r,g,b)/255, min=Math.min(r,g,b)/255, chroma=max-min
  const light=(max+min)/2
  if(max<0.18)return 'Black'
  if(chroma<0.18){if(light>0.7)return 'White';if(light<0.27)return 'Dark grey';return 'Grey'}
  if(chroma<0.26 && light>0.76)return 'White'
  const rn=r/255,gn=g/255,bn=b/255
  let hue=max===rn?(gn-bn)/chroma:max===gn?(bn-rn)/chroma+2:(rn-gn)/chroma+4
  hue=(hue*60+360)%360
  if(hue<18||hue>=345)return 'Red'
  if(hue<45)return light<0.45?'Brown':'Orange'
  if(hue<70)return 'Yellow'
  if(hue<165)return 'Green'
  if(hue<200)return 'Teal'
  if(hue<260)return 'Blue'
  if(hue<300)return 'Purple'
  return 'Pink'
}

const measurements=new Map<string,Promise<ColourEvidence>>()
export function measureColour(evidence:Evidence):Promise<ColourEvidence> {
  const polygon=evidence.effective_polygon || [
    [evidence.crop[0],evidence.crop[1]],[evidence.crop[0]+evidence.crop[2],evidence.crop[1]],
    [evidence.crop[0]+evidence.crop[2],evidence.crop[1]+evidence.crop[3]],[evidence.crop[0],evidence.crop[1]+evidence.crop[3]],
  ]
  const key=JSON.stringify([evidence.id,polygon,evidence.effective_mask_hash])
  if(measurements.has(key))return measurements.get(key)!
  const promise=(async()=>{
    let blob:Blob|null=null
    const response=await fetch(assetUrl(evidence.id)).catch(()=>null)
    if(response?.ok)blob=await response.blob()
    else blob=await loadImage(evidence.id)
    if(!blob)throw new Error('Colour evidence unavailable')
    const bitmap=await createImageBitmap(blob)
    try {
      const canvas=document.createElement('canvas');canvas.width=192;canvas.height=Math.round(192*evidence.height/evidence.width)
      const ctx=canvas.getContext('2d',{willReadFrequently:true})!
      ctx.beginPath();polygon.forEach(([x,y],i)=>{if(i===0)ctx.moveTo(x*canvas.width,y*canvas.height);else ctx.lineTo(x*canvas.width,y*canvas.height)})
      ctx.closePath();ctx.clip();ctx.drawImage(bitmap,0,0,canvas.width,canvas.height)
      const data=ctx.getImageData(0,0,canvas.width,canvas.height).data,channels:number[][]=[[],[],[]]
      for(let i=0;i<data.length;i+=4)if(data[i+3]>200)for(let c=0;c<3;c++)channels[c].push(data[i+c])
      if(channels[0].length<30)throw new Error('Insufficient crop pixels')
      const rgb=channels.map(values=>{values.sort((a,b)=>a-b);return values[Math.floor(values.length/2)]}) as [number,number,number]
      const xs=polygon.map(p=>p[0]),ys=polygon.map(p=>p[1])
      const left=Math.max(0,Math.min(...xs)),top=Math.max(0,Math.min(...ys))
      const width=Math.min(1,Math.max(...xs))-left,height=Math.min(1,Math.max(...ys))-top
      const thumb=document.createElement('canvas');thumb.width=120;thumb.height=120
      const t=thumb.getContext('2d')!;t.fillStyle='#ebe8e1';t.fillRect(0,0,120,120)
      t.drawImage(bitmap,left*bitmap.width,top*bitmap.height,width*bitmap.width,height*bitmap.height,0,0,120,120)
      return {name:colourName(rgb),rgb,swatch:`rgb(${rgb.join(',')})`,thumbnail:thumb.toDataURL('image/jpeg',0.85)}
    }finally{bitmap.close()}
  })()
  measurements.set(key,promise)
  promise.catch(()=>measurements.delete(key))
  return promise
}

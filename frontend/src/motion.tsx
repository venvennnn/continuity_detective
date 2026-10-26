import { useRef, type ButtonHTMLAttributes, type PointerEvent } from 'react'

export function MagneticButton({ className = '', children, ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  const ref = useRef<HTMLButtonElement>(null)
  function onMove(event: PointerEvent<HTMLButtonElement>) {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const el = ref.current
    if (!el || el.disabled) return
    const box = el.getBoundingClientRect()
    el.style.transform = `translate(${(event.clientX - box.left - box.width / 2) * 0.28}px, ${(event.clientY - box.top - box.height / 2) * 0.36}px)`
  }
  function onLeave() {
    if (ref.current) ref.current.style.transform = ''
  }
  return <button ref={ref} className={`magnetic ${className}`} onPointerMove={onMove} onPointerLeave={onLeave} {...props}>{children}</button>
}

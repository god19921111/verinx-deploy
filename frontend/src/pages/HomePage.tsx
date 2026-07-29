import { Link } from 'react-router-dom'
import { useState, useEffect, useRef } from 'react'

interface Particle {
  startX: number
  startY: number
  endX: number
  endY: number
  size: number
  delay: number
  duration: number
}

function generateParticles(cx: number, cy: number): Particle[] {
  const result: Particle[] = []
  const count = 100

  for (let i = 0; i < count; i++) {
    const angle = (Math.PI * 2 * i) / count + (Math.random() - 0.5) * 0.5
    const startRadius = 280 + Math.random() * 100
    const endRadius = Math.random() * 20

    result.push({
      startX: cx + Math.cos(angle) * startRadius,
      startY: cy + Math.sin(angle) * startRadius,
      endX: cx + Math.cos(angle) * endRadius,
      endY: cy + Math.sin(angle) * endRadius,
      size: 1.2 + Math.random() * 2.2,
      delay: Math.random() * 600,
      duration: 1800 + Math.random() * 1000,
    })
  }
  return result
}

function ParticleConvergence() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [showTitle, setShowTitle] = useState(false)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const dpr = window.devicePixelRatio || 1
    const rect = canvas.getBoundingClientRect()
    canvas.width = rect.width * dpr
    canvas.height = rect.height * dpr
    ctx.scale(dpr, dpr)

    const cx = rect.width / 2
    const cy = rect.height / 2
    const particles = generateParticles(cx, cy)

    const startTime = performance.now()
    let rafId: number

    const animate = (now: number) => {
      const elapsed = now - startTime
      ctx.clearRect(0, 0, rect.width, rect.height)

      let allDone = true

      particles.forEach((p) => {
        const timeSinceStart = elapsed - p.delay
        if (timeSinceStart < 0) {
          allDone = false
          ctx.beginPath()
          ctx.arc(p.startX, p.startY, p.size, 0, Math.PI * 2)
          ctx.fillStyle = 'rgba(240, 240, 250, 0.9)'
          ctx.fill()
          return
        }

        const progress = Math.min(timeSinceStart / p.duration, 1)
        if (progress < 1) allDone = false

        const easeProgress = 1 - Math.pow(1 - progress, 3)
        const x = p.startX + (p.endX - p.startX) * easeProgress
        const y = p.startY + (p.endY - p.startY) * easeProgress
        const opacity = 0.9 * (1 - progress * 0.85)
        const r = p.size * (1 - progress * 0.8)

        ctx.beginPath()
        ctx.arc(x, y, Math.max(r, 0.1), 0, Math.PI * 2)
        ctx.fillStyle = `rgba(240, 240, 250, ${Math.max(opacity, 0)})`
        ctx.fill()
      })

      if (!allDone) {
        rafId = requestAnimationFrame(animate)
      }
    }

    rafId = requestAnimationFrame(animate)
    const t = setTimeout(() => setShowTitle(true), 2600)

    return () => {
      cancelAnimationFrame(rafId)
      clearTimeout(t)
    }
  }, [])

  return (
    <div className="relative w-full h-[280px] flex items-center justify-center">
      <canvas
        ref={canvasRef}
        style={{ width: '100%', height: '100%', display: 'block' }}
      />
      {showTitle && (
        <div
          className="absolute inset-0 flex items-center justify-center pointer-events-none"
          style={{ animation: 'fadeInTitle 1000ms ease-out forwards' }}
        >
          <span
            className="text-[56px] md:text-[64px] font-bold tracking-[0.08em] text-[#F0F0FA]"
            style={{
              fontFamily: 'Inter, SF Pro Display, sans-serif',
              textShadow: '0 0 24px rgba(240,240,250,0.25), 0 0 48px rgba(240,240,250,0.1)',
            }}
          >
            VERINX
          </span>
        </div>
      )}
      <style>{`
        @keyframes fadeInTitle {
          0% { opacity: 0; transform: translateY(4px); }
          100% { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  )
}

export function HomePage() {
  const [showSubtitle, setShowSubtitle] = useState(false)
  const [showButtons, setShowButtons] = useState(false)
  const [showTopLabel, setShowTopLabel] = useState(false)

  useEffect(() => {
    const t0 = setTimeout(() => setShowTopLabel(true), 300)
    const t1 = setTimeout(() => setShowSubtitle(true), 3600)
    const t2 = setTimeout(() => setShowButtons(true), 4600)
    return () => {
      clearTimeout(t0)
      clearTimeout(t1)
      clearTimeout(t2)
    }
  }, [])

  return (
    <div className="min-h-[calc(100vh-64px)] flex flex-col items-center justify-center px-6 relative">
      <div className="absolute inset-0 bg-black" />

      <div className="relative z-10 text-center max-w-4xl w-full flex flex-col items-center">
        <div
          className="text-xs uppercase-spacex text-[#808080] tracking-[0.3em] mb-2"
          style={{
            opacity: showTopLabel ? 1 : 0,
            transition: 'opacity 600ms ease-out',
          }}
        >
          AI-POWERED INTERVIEW PREPARATION
        </div>

        <ParticleConvergence />

        <div
          className="mt-2"
          style={{
            opacity: showSubtitle ? 1 : 0,
            transform: showSubtitle ? 'translateY(0)' : 'translateY(8px)',
            transition: 'all 1200ms cubic-bezier(0.19, 1, 0.22, 1)',
          }}
        >
          <p className="text-lg md:text-xl text-[rgba(240,240,250,0.8)] font-body tracking-wide leading-relaxed">
            求真思辨 面见未来
          </p>
        </div>

        <div
          className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4"
          style={{
            opacity: showButtons ? 1 : 0,
            transform: showButtons ? 'translateY(0)' : 'translateY(12px)',
            transition: 'all 1000ms cubic-bezier(0.19, 1, 0.22, 1)',
          }}
        >
          <Link
            to="/practice/full"
            className="group w-full sm:w-auto border border-[rgba(240,240,250,0.35)] px-10 py-4 hover:bg-[rgba(240,240,250,0.1)] transition-spacex"
          >
            <span className="text-xs uppercase-spacex tracking-[0.15em]">
              开始练习
            </span>
          </Link>
          <Link
            to="/login"
            className="group w-full sm:w-auto border border-[rgba(240,240,250,0.35)] px-10 py-4 hover:bg-[rgba(240,240,250,0.1)] transition-spacex"
          >
            <span className="text-xs uppercase-spacex tracking-[0.15em]">
              登录账号
            </span>
          </Link>
        </div>
      </div>

      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 z-10">
        <span className="text-[10px] uppercase-spacex text-[#808080] tracking-[0.2em]">
          AI 引擎在线
        </span>
        <span className="w-2 h-2 bg-[#22c55e] animate-pulse" />
      </div>
    </div>
  )
}

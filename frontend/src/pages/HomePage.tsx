import { Link, useNavigate } from 'react-router-dom'
import { useState, useEffect, useRef } from 'react'
import { useAuthStore } from '../store/authStore'
import api from '@/lib/api'
import type { CheckinStatus } from '@/types'
import { BouncyWrap } from '@/components/BouncyButton'

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
      <canvas ref={canvasRef} style={{ width: '100%', height: '100%', display: 'block' }} />
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

const TIER_META = {
  synapse: { name: 'SYNAPSE', icon: '⟁', color: '#6b7280' },
  quantum: { name: 'QUANTUM', icon: '◈', color: '#22d3ee' },
  singularity: { name: 'SINGULARITY', icon: '◉', color: '#818cf8' },
  transcend: { name: 'TRANSCEND', icon: '◐', color: '#f0f0fa' },
}

export function HomePage() {
  const navigate = useNavigate()
  const [showSubtitle, setShowSubtitle] = useState(false)
  const [showButtons, setShowButtons] = useState(false)
  const [showTopLabel, setShowTopLabel] = useState(false)
  const { isAuthenticated, user } = useAuthStore()

  const [checkin, setCheckin] = useState<CheckinStatus | null>(null)
  const [highScore, setHighScore] = useState(0)
  const [loading, setLoading] = useState(false)

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

  useEffect(() => {
    if (!isAuthenticated) return
    setLoading(true)
    api.get('/stats/checkin-status')
      .then((r) => setCheckin(r.data.data || r.data))
      .catch(() => {})
    const stored = localStorage.getItem('verinx_challenge_highscore')
    if (stored) setHighScore(parseFloat(stored))
    setLoading(false)
  }, [isAuthenticated])

  const today = new Date()
  const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  const todayStr = `${today.getMonth() + 1}月${today.getDate()}日 · ${weekdays[today.getDay()]}`

  const currentTier = (() => {
    const streak = checkin?.streak_days ?? 0
    if (streak >= 365) return { tier: 'transcend', ...TIER_META.transcend }
    if (streak >= 100) return { tier: 'singularity', ...TIER_META.singularity }
    if (streak >= 30) return { tier: 'quantum', ...TIER_META.quantum }
    if (streak >= 7) return { tier: 'synapse', ...TIER_META.synapse }
    return null
  })()

  if (isAuthenticated) {
    return (
      <div className="min-h-[calc(100vh-64px)] flex flex-col items-center justify-center px-6 py-16 bg-black">
        <div className="max-w-lg mx-auto w-full">
          {/* 双模式卡片 —— 居中放大 */}
          <div className="space-y-4">
            {/* 每日打卡 */}
            <Link
              to="/checkin"
              className="group block border border-[rgba(240,240,250,0.08)] p-8 hover:border-[rgba(240,240,250,0.2)] transition-spacex text-center"
            >
              <div className="text-[11px] uppercase-spacex tracking-[0.2em] text-[#808080] mb-3">
                每日打卡
              </div>
              {checkin && checkin.streak_days > 0 ? (
                <div className="flex items-baseline justify-center gap-2">
                  <span
                    className="font-display tabular-nums text-[#F0F0FA] leading-none"
                    style={{ fontSize: '72px' }}
                  >
                    {checkin.streak_days}
                  </span>
                  <span className="text-xs uppercase-spacex tracking-[0.15em] text-[#808080]">
                    天连胜
                  </span>
                </div>
              ) : (
                <div className="text-sm text-[rgba(240,240,250,0.4)] py-4">
                  开始第一天
                </div>
              )}
              <div className="mt-4 flex items-center justify-center gap-1 text-[rgba(240,240,250,0.35)] group-hover:text-[rgba(240,240,250,0.7)] transition-spacex">
                <span className="text-[10px] uppercase-spacex tracking-[0.15em]">
                  {checkin?.checked_today ? '已完成' : '去打卡'}
                </span>
                <svg
                  width="10"
                  height="10"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="square"
                  className="transition-transform group-hover:translate-x-0.5"
                >
                  <path d="M5 12h14M13 5l7 7-7 7" />
                </svg>
              </div>
            </Link>

            {/* 极限挑战 */}
            <Link
              to="/challenge"
              className="group block border border-[rgba(240,240,250,0.08)] p-8 hover:border-[rgba(240,240,250,0.2)] transition-spacex text-center"
            >
              <div className="text-[11px] uppercase-spacex tracking-[0.2em] text-[#808080] mb-3">
                极限挑战
              </div>
              {highScore > 0 ? (
                <div className="flex items-baseline justify-center gap-2">
                  <span
                    className="font-display tabular-nums text-[#F0F0FA] leading-none"
                    style={{ fontSize: '72px' }}
                  >
                    {Math.round(highScore)}
                  </span>
                  <span className="text-xs uppercase-spacex tracking-[0.15em] text-[#808080]">
                    最高分
                  </span>
                </div>
              ) : (
                <div className="text-sm text-[rgba(240,240,250,0.4)] py-4">
                  暂无记录
                </div>
              )}
              <div className="mt-4 flex items-center justify-center gap-1 text-[rgba(240,240,250,0.35)] group-hover:text-[rgba(240,240,250,0.7)] transition-spacex">
                <span className="text-[10px] uppercase-spacex tracking-[0.15em]">去挑战</span>
                <svg
                  width="10"
                  height="10"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="square"
                  className="transition-transform group-hover:translate-x-0.5"
                >
                  <path d="M5 12h14M13 5l7 7-7 7" />
                </svg>
              </div>
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-[calc(100vh-64px)] flex flex-col items-center px-6 relative pt-16 pb-24">
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

        {/* 主入口 */}
        <div
          className="mt-8 flex flex-col items-center"
          style={{
            opacity: showButtons ? 1 : 0,
            transform: showButtons ? 'translateY(0)' : 'translateY(12px)',
            transition: 'all 1000ms cubic-bezier(0.19, 1, 0.22, 1)',
          }}
        >
          <button
            onClick={() => navigate('/login')}
            className="border border-[rgba(240,240,250,0.35)] px-16 py-5 hover:bg-[rgba(240,240,250,0.1)] transition-spacex"
          >
            <span className="text-xs uppercase-spacex tracking-[0.15em]">
              登录开始
            </span>
          </button>
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

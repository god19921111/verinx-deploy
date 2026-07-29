import { cn } from '@/lib/utils'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'

interface ScoreCardProps {
  overall: number
  scores: {
    analysis: number
    expression: number
    adaptability: number
    organization: number
  }
  weights: {
    analysis: number
    expression: number
    adaptability: number
    organization: number
  }
  reportContent?: string
  dimensionAnalysis?: {
    analysis?: string
    expression?: string
    adaptability?: string
    organization?: string
  }
  deductionPoints?: string
  optimizationSuggestions?: string
}

const dimensionLabels: Record<string, string> = {
  analysis: '综合分析',
  expression: '言语表达',
  adaptability: '应急应变',
  organization: '组织管理',
}

function getScoreColor(score: number): string {
  if (score >= 80) return 'text-[#F0F0FA]'
  if (score >= 60) return 'text-[rgba(240,240,250,0.8)]'
  return 'text-[rgba(240,240,250,0.6)]'
}

function getScoreLevel(score: number): { label: string; color: string } {
  if (score >= 80) return { label: 'EXCELLENT', color: 'text-[#F0F0FA]' }
  if (score >= 70) return { label: 'GOOD', color: 'text-[rgba(240,240,250,0.8)]' }
  if (score >= 60) return { label: 'PASS', color: 'text-[rgba(240,240,250,0.7)]' }
  return { label: 'IMPROVE', color: 'text-[rgba(240,240,250,0.5)]' }
}

function DimensionBar({ keyName, score, weight, analysis }: { keyName: string; score: number; weight: number; analysis?: string }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="border border-[rgba(240,240,250,0.35)]">
      <div
        className="flex items-center justify-between p-4 cursor-pointer hover:bg-[rgba(240,240,250,0.05)] transition-spacex"
        onClick={() => analysis && setExpanded(!expanded)}
      >
        <div className="flex items-center gap-4">
          <span className="text-xs uppercase-spacex tracking-[0.1em] text-[#808080]">
            {dimensionLabels[keyName]}
          </span>
          <span className="text-[10px] uppercase-spacex text-[rgba(240,240,250,0.5)]">
            WEIGHT {Math.round(weight * 100)}%
          </span>
        </div>
        <div className="flex items-center gap-4">
          <span
            className={cn(
              'text-2xl font-bold tabular-nums',
              getScoreColor(score),
            )}
          >
            {score}
          </span>
          {analysis && (
            expanded ? (
              <ChevronUp className="w-4 h-4 text-[rgba(240,240,250,0.5)]" />
            ) : (
              <ChevronDown className="w-4 h-4 text-[rgba(240,240,250,0.5)]" />
            )
          )}
        </div>
      </div>
      <div className="px-4 pb-4">
        <div className="h-1 w-full bg-[rgba(240,240,250,0.1)]">
          <div
            className="h-full bg-[#F0F0FA] transition-all duration-700"
            style={{ width: `${score}%` }}
          />
        </div>
      </div>
      {analysis && expanded && (
        <div className="px-4 pb-4 pt-2 border-t border-[rgba(240,240,250,0.2)]">
          <p className="text-sm text-[rgba(240,240,250,0.7)] font-body leading-relaxed">
            {analysis}
          </p>
        </div>
      )}
    </div>
  )
}

export function ScoreCard({ overall, scores, weights, reportContent, dimensionAnalysis, deductionPoints, optimizationSuggestions }: ScoreCardProps) {
  const dimensions = Object.keys(scores) as (keyof typeof scores)[]
  const level = getScoreLevel(overall)

  return (
    <div className="border border-[rgba(240,240,250,0.35)]">
      <div className="border-b border-[rgba(240,240,250,0.35)] p-6">
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 bg-[#F0F0FA] animate-pulse" />
          <span className="text-xs uppercase-spacex tracking-[0.2em] text-[#808080]">
            SCORE REPORT
          </span>
        </div>
      </div>

      <div className="p-12 text-center">
        <div className="text-xs uppercase-spacex tracking-[0.3em] text-[#808080] mb-6">
          OVERALL SCORE
        </div>
        <div className="flex items-baseline justify-center gap-4">
          <span className="text-8xl font-bold tabular-nums text-[#F0F0FA]">
            {overall}
          </span>
          <span className="text-xs uppercase-spacex tracking-[0.2em]">
            / 100
          </span>
        </div>
        <div className="mt-6 border-t border-[rgba(240,240,250,0.35)] w-32 mx-auto" />
        <div className={`mt-6 text-xs uppercase-spacex tracking-[0.3em] ${level.color}`}>
          {level.label}
        </div>
        <p className="mt-4 text-xs text-[#808080] uppercase-spacex tracking-[0.1em]">
          FOUR DIMENSION ANALYSIS
        </p>
      </div>

      {reportContent && (
        <div className="border-t border-[rgba(240,240,250,0.35)] p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-1 h-4 bg-[#F0F0FA]" />
            <span className="text-xs uppercase-spacex tracking-[0.2em] text-[#808080]">
              EXAMINER COMMENT
            </span>
          </div>
          <p className="text-[rgba(240,240,250,0.8)] font-body leading-relaxed">
            {reportContent}
          </p>
        </div>
      )}

      <div className="border-t border-[rgba(240,240,250,0.35)] p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-1 h-4 bg-[#F0F0FA]" />
          <span className="text-xs uppercase-spacex tracking-[0.2em] text-[#808080]">
            DIMENSION ANALYSIS
          </span>
        </div>
        <div className="space-y-4">
          {dimensions.map((key) => (
            <DimensionBar
              key={key}
              keyName={key}
              score={scores[key]}
              weight={weights[key]}
              analysis={dimensionAnalysis?.[key]}
            />
          ))}
        </div>
      </div>

      {deductionPoints && (
        <div className="border-t border-[rgba(240,240,250,0.35)] p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-1 h-4 bg-[rgba(239,68,68,0.9)]" />
            <span className="text-xs uppercase-spacex tracking-[0.2em] text-[rgba(239,68,68,0.9)]">
              AREAS TO IMPROVE
            </span>
          </div>
          <ul className="space-y-3">
            {deductionPoints.split('；').map((point, idx) => {
              const cleanPoint = point.replace(/^\d+\.\s*/, '').trim()
              if (!cleanPoint) return null
              return (
                <li key={idx} className="flex items-start gap-3">
                  <span className="text-[rgba(239,68,68,0.9)] mt-1">—</span>
                  <span className="text-sm text-[rgba(240,240,250,0.7)] font-body">
                    {cleanPoint}
                  </span>
                </li>
              )
            })}
          </ul>
        </div>
      )}

      {optimizationSuggestions && (
        <div className="border-t border-[rgba(240,240,250,0.35)] p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-1 h-4 bg-[#F0F0FA]" />
            <span className="text-xs uppercase-spacex tracking-[0.2em] text-[#F0F0FA]">
              RECOMMENDATIONS
            </span>
          </div>
          <ul className="space-y-3">
            {optimizationSuggestions.split('；').map((point, idx) => {
              const cleanPoint = point.replace(/^\d+\.\s*/, '').trim()
              if (!cleanPoint) return null
              return (
                <li key={idx} className="flex items-start gap-3">
                  <span className="text-[#F0F0FA] mt-1">—</span>
                  <span className="text-sm text-[rgba(240,240,250,0.7)] font-body">
                    {cleanPoint}
                  </span>
                </li>
              )
            })}
          </ul>
        </div>
      )}
    </div>
  )
}

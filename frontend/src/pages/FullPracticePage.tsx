import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ExamTimer } from '@/components/ExamTimer'
import { QuestionCard } from '@/components/QuestionCard'
import { ScoreCard } from '@/components/ScoreCard'
import { DisclaimerBanner } from '@/components/DisclaimerBanner'
import api from '@/lib/api'
import type { Question } from '@/types'
import { useAuthStore } from '@/store/authStore'

type Step = 'waiting' | 'thinking' | 'answering' | 'scoring'

const steps: { key: Step; label: string; maxSeconds: number }[] = [
  { key: 'waiting', label: '候考', maxSeconds: 30 },
  { key: 'thinking', label: '思考', maxSeconds: 120 },
  { key: 'answering', label: '答题', maxSeconds: 240 },
  { key: 'scoring', label: '评分', maxSeconds: 0 },
]

export function FullPracticePage() {
  const navigate = useNavigate()
  const { isAuthenticated } = useAuthStore()

  const [currentStep, setCurrentStep] = useState<Step>('waiting')
  const [question, setQuestion] = useState<Question | null>(null)
  const [answerText, setAnswerText] = useState('')
  const [practiceId, setPracticeId] = useState<string | null>(null)
  const [scoreResult, setScoreResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [timerKey, setTimerKey] = useState(0)
  const [submitError, setSubmitError] = useState<string | null>(null)

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login')
    }
  }, [isAuthenticated, navigate])

  const stepIndex = steps.findIndex((s) => s.key === currentStep)

  const fetchQuestion = async () => {
    try {
      const res = await api.post('/ai/generate-question', null, {
        params: { random_category: true },
        timeout: 60000,
      })
      const data = res.data.data || res.data
      setQuestion({
        id: 'ai-generated',
        content: data.content,
        category: data.category || '综合分析',
        difficulty: data.difficulty || 3,
        answer_reference: data.answer_reference || '',
        exam_type: '省考',
        created_at: new Date().toISOString(),
      })
    } catch {
      try {
        const res = await api.get('/questions', { params: { page_size: 1, page: 1 } })
        const data = res.data.data || res.data
        const items = data.items || data.list || []
        if (items.length > 0) {
          setQuestion(items[0])
        }
      } catch {
        // leave question null
      }
    }
  }

  const goNext = () => {
    const idx = stepIndex
    if (idx < steps.length - 1) {
      setCurrentStep(steps[idx + 1].key)
      setTimerKey((k) => k + 1)
    }
  }

  const handleStartMock = async () => {
    setLoading(true)
    await fetchQuestion()
    setLoading(false)
    goNext()
  }

  const handleSubmitAnswer = async () => {
    if (!question) return
    if (!answerText.trim()) {
      setSubmitError('请先输入答案')
      return
    }
    setSubmitError(null)
    setLoading(true)
    const mainAnswer = answerText

    setCurrentStep('scoring')
    setTimerKey((k) => k + 1)

    try {
      try {
        const practiceRes = await api.post('/practice', {
          question_id: question.id,
          practice_mode: 'full',
          answer_text: mainAnswer,
        })
        const record = practiceRes.data.data || practiceRes.data
        setPracticeId(record.id)
      } catch {
        // ignore
      }

      const scoreRes = await api.post('/ai/score', {
        question_content: question.content,
        answer_text: mainAnswer,
        question_category: question.category,
      }, { timeout: 120000 })
      const scoreData = scoreRes.data.data || scoreRes.data
      setScoreResult(scoreData)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  const handleThinkingTimeout = () => {
    setCurrentStep('answering')
    setTimerKey((k) => k + 1)
  }

  const handleAnsweringTimeout = () => {
    if (answerText.trim()) {
      handleSubmitAnswer()
    }
  }

  const handleRetry = () => {
    setCurrentStep('waiting')
    setQuestion(null)
    setAnswerText('')
    setScoreResult(null)
    setLoading(false)
    setTimerKey((k) => k + 1)
    setSubmitError(null)
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-12">
      <div className="text-xs uppercase-spacex text-[#808080] tracking-[0.2em] mb-8">
        FULL SIMULATION
      </div>
      <h1 className="font-display text-3xl md:text-4xl tracking-tight">
        全真模拟
      </h1>

      <div className="mt-12">
        <div className="flex items-center">
          {steps.map((s, i) => (
            <div key={s.key} className="flex-1 flex flex-col items-center">
              <div className={`w-10 h-10 flex items-center justify-center text-xs font-bold border transition-spacex ${
                i < stepIndex
                  ? 'border-[#F0F0FA] bg-[#F0F0FA] text-black'
                  : i === stepIndex
                  ? 'border-[#F0F0FA] bg-transparent text-[#F0F0FA]'
                  : 'border-[rgba(240,240,250,0.35)] text-[#808080]'
              }`}>
                {i < stepIndex ? '✓' : i + 1}
              </div>
              <span className={`mt-2 text-xs uppercase-spacex tracking-[0.1em] ${
                i <= stepIndex ? 'text-[#F0F0FA]' : 'text-[#808080]'
              }`}>
                {s.label}
              </span>
            </div>
          ))}
        </div>
        <div className="mt-3 flex items-center gap-2">
          {steps.map((s, i) => (
            <div
              key={s.key}
              className={`flex-1 h-px transition-spacex ${
                i <= stepIndex ? 'bg-[#F0F0FA]' : 'bg-[rgba(240,240,250,0.35)]'
              }`}
            />
          ))}
        </div>
      </div>

      {currentStep !== 'waiting' && currentStep !== 'scoring' && (
        <div className="mt-12">
          <ExamTimer
            key={timerKey}
            mode={currentStep === 'thinking' ? 'thinking' : 'answering'}
            maxSeconds={steps[stepIndex].maxSeconds}
            onTimeout={
              currentStep === 'thinking' ? handleThinkingTimeout :
              handleAnsweringTimeout
            }
            isRunning={true}
          />
        </div>
      )}

      <div className="mt-12">
        {currentStep === 'waiting' && (
          <div className="border border-[rgba(240,240,250,0.35)] p-12 text-center">
            <p className="text-[rgba(240,240,250,0.7)] font-body">全真模拟即将开始，请做好准备</p>
            <p className="mt-3 text-sm text-[#808080]">流程：候考(30s) → 思考(2min) → 答题(4min) → 评分</p>
            <button 
              className="mt-8 border border-[rgba(240,240,250,0.35)] px-12 py-4 hover:bg-[rgba(240,240,250,0.1)] transition-spacex"
              onClick={handleStartMock} 
              disabled={loading}
            >
              <span className="text-xs uppercase-spacex tracking-[0.15em]">
                {loading ? 'AI出题中...' : '开始模拟'}
              </span>
            </button>
          </div>
        )}

        {currentStep === 'thinking' && question && (
          <div className="space-y-8">
            <QuestionCard question={question} />
            <p className="text-sm text-[#808080] text-center">请在规定时间内思考，准备好后点击"开始答题"</p>
            <div className="text-center">
              <button 
                className="border border-[rgba(240,240,250,0.35)] px-12 py-4 hover:bg-[rgba(240,240,250,0.1)] transition-spacex"
                onClick={() => { setCurrentStep('answering'); setTimerKey((k) => k + 1) }}
              >
                <span className="text-xs uppercase-spacex tracking-[0.15em]">
                  开始答题
                </span>
              </button>
            </div>
          </div>
        )}

        {currentStep === 'answering' && (
          <div className="space-y-8">
            {question && (
              <div className="border border-[rgba(240,240,250,0.35)] p-8">
                <p className="text-[rgba(240,240,250,0.9)] font-body leading-relaxed">{question.content}</p>
              </div>
            )}

            <div>
              <label className="block text-xs uppercase-spacex tracking-[0.1em] text-[#808080] mb-4">
                文字作答
              </label>
              <textarea
                value={answerText}
                onChange={(e) => setAnswerText(e.target.value)}
                placeholder="请在此输入你的答案..."
                rows={8}
                className="w-full border border-[rgba(240,240,250,0.35)] bg-transparent px-4 py-4 text-[#F0F0FA] font-body placeholder:text-[#808080] focus:border-[#F0F0FA] focus:outline-none resize-none transition-spacex"
              />
            </div>

            {submitError && (
              <p className="text-sm text-[rgba(239,68,68,0.9)] text-center">{submitError}</p>
            )}

            <button
              className="w-full border border-[rgba(240,240,250,0.35)] px-12 py-4 hover:bg-[rgba(240,240,250,0.1)] transition-spacex disabled:opacity-50"
              onClick={handleSubmitAnswer}
              disabled={loading}
            >
              <span className="text-xs uppercase-spacex tracking-[0.15em]">
                {loading ? 'AI评分中...' : '提交答案'}
              </span>
            </button>
          </div>
        )}

        {currentStep === 'scoring' && !scoreResult && (
          <div className="border border-[rgba(240,240,250,0.35)] p-12 text-center">
            <p className="font-display text-xl tracking-tight">答题结束</p>
            <p className="mt-3 text-sm text-[#808080]">
              {loading ? 'AI正在生成评分报告...' : '评分报告生成中...'}
            </p>
          </div>
        )}

        {currentStep === 'scoring' && scoreResult && (
          <div className="space-y-8">
            <ScoreCard
              overall={scoreResult.score_overall ?? 0}
              scores={{
                analysis: scoreResult.score_analysis ?? 0,
                expression: scoreResult.score_expression ?? 0,
                adaptability: scoreResult.score_adaptability ?? 0,
                organization: scoreResult.score_organization ?? 0,
              }}
              weights={{
                analysis: scoreResult.weights?.analysis ?? 0.30,
                expression: scoreResult.weights?.expression ?? 0.25,
                adaptability: scoreResult.weights?.adaptability ?? 0.25,
                organization: scoreResult.weights?.organization ?? 0.20,
              }}
              reportContent={scoreResult.report_content}
              dimensionAnalysis={scoreResult.dimension_analysis}
              deductionPoints={scoreResult.deduction_points}
              optimizationSuggestions={scoreResult.optimization_suggestions}
            />

            <button 
              className="w-full border border-[rgba(240,240,250,0.35)] px-12 py-4 hover:bg-[rgba(240,240,250,0.1)] transition-spacex"
              onClick={handleRetry}
            >
              <span className="text-xs uppercase-spacex tracking-[0.15em]">
                再来一次
              </span>
            </button>

            <div className="mt-8">
              <DisclaimerBanner />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

/** 题型分类 */
export type QuestionCategory =
  | '综合分析'
  | '人际沟通'
  | '应急应变'
  | '组织管理'
  | '自我认知'

/** 考试类型 */
export type ExamType = '国考' | '省考' | '事业单位'

/** 题目 */
export interface Question {
  id: string
  category: QuestionCategory
  exam_type: ExamType
  content: string
  difficulty: number
  answer_reference: string | null
  created_at: string
}

/** 练习模式 */
export type PracticeMode = 'single' | 'full'

/** 练习记录 */
export interface PracticeRecord {
  id: string
  user_id: string
  question_id: string
  question?: Question
  practice_mode: PracticeMode
  thinking_time: number | null
  answer_time: number | null
  answer_text: string | null
  audio_url: string | null
  video_url: string | null
  score_overall: number | null
  score_analysis: number | null
  score_expression: number | null
  score_adaptability: number | null
  score_organization: number | null
  score_appearance: number | null
  report_content: string | null
  dimension_analysis: Record<string, string> | null
  deduction_points: string | null
  optimization_suggestions: string | null
  follow_ups: FollowUpRecord[]
  created_at: string
}

/** 追问记录 */
export interface FollowUpRecord {
  id: string
  practice_record_id: string
  question_text: string
  answer_text: string | null
  audio_url: string | null
  created_at: string
}

/** 用户 */
export interface User {
  id: string
  phone: string
  name: string | null
  avatar: string | null
  member_type: 'free' | 'premium'
  member_expire_at: string | null
  daily_practice_count: number
  last_practice_date: string | null
  total_practice_count: number
  avg_score: number
}

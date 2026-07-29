import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { Card, CardContent } from '@/components/ui/Card'
import api from '@/lib/api'
import type { PracticeRecord, PracticeMode } from '@/types'

export function HistoryPage() {
  const [records, setRecords] = useState<PracticeRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [filterMode, setFilterMode] = useState<'all' | 'single' | 'full'>('all')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)

  useEffect(() => {
    const params: Record<string, string> = {
      page: String(page),
      page_size: '10',
    }
    if (filterMode !== 'all') params.practice_mode = filterMode

    setLoading(true)
    api.get('/practice', { params })
      .then((res) => {
        const data = res.data.data || res.data
        setRecords(data.items || data.list || [])
        setTotalPages(data.total_pages || Math.ceil((data.total || 0) / 10) || 1)
      })
      .catch(() => setRecords([]))
      .finally(() => setLoading(false))
  }, [filterMode, page])

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr)
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900">练习历史</h1>

      {/* Filter Bar */}
      <div className="mt-4 flex flex-wrap gap-2">
        {([
          { key: 'all' as const, label: '全部' },
          { key: 'single' as const, label: '专项训练' },
          { key: 'full' as const, label: '全真模拟' },
        ]).map((f) => (
          <Button
            key={f.key}
            variant={filterMode === f.key ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => { setFilterMode(f.key); setPage(1) }}
          >
            {f.label}
          </Button>
        ))}
      </div>

      {/* History List */}
      <div className="mt-6 space-y-3">
        {loading && (
          <div className="py-12 text-center text-gray-400">加载中...</div>
        )}
        {!loading && records.length === 0 && (
          <div className="py-12 text-center text-gray-400">暂无练习记录</div>
        )}
        {!loading && records.map((r) => (
          <Link
            key={r.id}
            to={`/report/${r.id}`}
            className="block"
          >
            <Card className="hover:shadow-md transition-shadow">
              <CardContent className="py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="flex flex-col items-center text-center shrink-0 w-12">
                      <div className="text-lg font-bold text-gray-900">
                        {r.score_overall ?? '-'}
                      </div>
                      <div className="text-xs text-gray-400">分</div>
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <Badge variant="default">
                          {r.question?.category ?? '未知'}
                        </Badge>
                        <Badge variant={
                          r.practice_mode === 'full' ? 'warning' : 'success'
                        }>
                          {r.practice_mode === 'full' ? '全真模拟' : '专项训练'}
                        </Badge>
                      </div>
                      <div className="mt-1 text-xs text-gray-400">
                        {formatDate(r.created_at)}
                      </div>
                    </div>
                  </div>
                  <div className="text-sm text-primary hover:underline shrink-0 ml-2">
                    查看报告
                  </div>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="mt-6 flex items-center justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
          >
            上一页
          </Button>
          <span className="text-sm text-gray-500">{page} / {totalPages}</span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            下一页
          </Button>
        </div>
      )}
    </div>
  )
}

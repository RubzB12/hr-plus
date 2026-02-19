'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { GitBranch, Users, TrendingDown, ArrowUpRight, ExternalLink } from 'lucide-react'

interface Requisition {
  id: string
  requisition_id: string
  title: string
  status: string
  department: { id: string; name: string }
  hiring_manager: { id: string; user: { first_name: string; last_name: string } }
  recruiter: { id: string; user: { first_name: string; last_name: string } }
  headcount: number
  filled_count: number
  opened_at: string | null
  created_at: string
}

interface PipelineMetric {
  stage: string
  count?: number
  conversion_rate?: number
}

const STAGE_COLORS: Record<string, string> = {
  Applied: '#3b82f6',
  Screening: '#8b5cf6',
  Interview: '#f59e0b',
  Offer: '#10b981',
  Hired: '#059669',
}

const DEFAULT_STAGE_COLOR = '#94a3b8'

function getDaysOpen(openedAt: string | null, createdAt: string): number {
  const date = openedAt ? new Date(openedAt) : new Date(createdAt)
  return Math.floor((Date.now() - date.getTime()) / (1000 * 60 * 60 * 24))
}

function HeadcountBar({ filled, total }: { filled: number; total: number }) {
  const pct = total > 0 ? Math.min((filled / total) * 100, 100) : 0
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full bg-muted overflow-hidden">
        <div
          className="h-full rounded-full bg-primary transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-muted-foreground whitespace-nowrap">
        {filled}/{total}
      </span>
    </div>
  )
}

export function PipelineOverviewClient() {
  const [loading, setLoading] = useState(true)
  const [requisitions, setRequisitions] = useState<Requisition[]>([])
  const [pipelineMetrics, setPipelineMetrics] = useState<PipelineMetric[]>([])
  const [totalActive, setTotalActive] = useState(0)
  const [avgTimeToFill, setAvgTimeToFill] = useState<number | null>(null)

  useEffect(() => {
    async function load() {
      setLoading(true)
      try {
        const api = process.env.NEXT_PUBLIC_API_URL

        const [reqRes, execRes] = await Promise.allSettled([
          fetch(`${api}/api/v1/internal/requisitions/?status=open`, {
            credentials: 'include',
          }).then((r) => (r.ok ? r.json() : { results: [] })),
          fetch(`${api}/api/v1/internal/analytics/dashboard/executive/`, {
            credentials: 'include',
          }).then((r) => (r.ok ? r.json() : null)),
        ])

        if (reqRes.status === 'fulfilled') {
          setRequisitions(reqRes.value?.results ?? [])
        }

        if (execRes.status === 'fulfilled' && execRes.value) {
          const exec = execRes.value
          if (exec.pipeline_metrics) {
            setPipelineMetrics(exec.pipeline_metrics)
          }
          if (exec.total_active_candidates != null) {
            setTotalActive(exec.total_active_candidates)
          } else if (exec.active_candidates != null) {
            setTotalActive(exec.active_candidates)
          }
          if (exec.avg_time_to_fill != null) {
            setAvgTimeToFill(exec.avg_time_to_fill)
          }
        }
      } catch (err) {
        console.error('Pipeline overview load error:', err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const openReqs = requisitions.length
  const totalHeadcount = requisitions.reduce((s, r) => s + r.headcount, 0)
  const filledHeadcount = requisitions.reduce((s, r) => s + r.filled_count, 0)

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid gap-4 md:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="p-6">
                <div className="h-16 bg-muted rounded" />
              </CardContent>
            </Card>
          ))}
        </div>
        <Card className="animate-pulse">
          <CardContent className="p-6">
            <div className="h-64 bg-muted rounded" />
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* KPI row */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Open Requisitions</CardTitle>
            <div className="rounded-full p-2 bg-blue-50">
              <GitBranch className="h-4 w-4 text-blue-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{openReqs}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {filledHeadcount}/{totalHeadcount} headcount filled
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Candidates</CardTitle>
            <div className="rounded-full p-2 bg-green-50">
              <Users className="h-4 w-4 text-green-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalActive}</div>
            <p className="text-xs text-muted-foreground mt-1">Across all open pipelines</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Time to Fill</CardTitle>
            <div className="rounded-full p-2 bg-orange-50">
              <TrendingDown className="h-4 w-4 text-orange-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {avgTimeToFill != null ? `${avgTimeToFill}d` : '—'}
            </div>
            <p className="text-xs text-muted-foreground mt-1">Days from open to hire</p>
          </CardContent>
        </Card>
      </div>

      {/* Funnel chart */}
      {pipelineMetrics.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Pipeline Funnel</CardTitle>
            <p className="text-sm text-muted-foreground">Conversion rates across hiring stages</p>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart
                data={pipelineMetrics}
                margin={{ top: 8, right: 16, left: 0, bottom: 8 }}
              >
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="stage" tick={{ fontSize: 12 }} />
                <YAxis
                  tickFormatter={(v: number) => `${v}%`}
                  tick={{ fontSize: 12 }}
                  domain={[0, 100]}
                />
                <Tooltip
                  formatter={(value: number | string | undefined) => [
                    `${value ?? 0}%`,
                    'Conversion Rate',
                  ]}
                />
                <Bar dataKey="conversion_rate" radius={[4, 4, 0, 0]}>
                  {pipelineMetrics.map((entry) => (
                    <Cell
                      key={entry.stage}
                      fill={STAGE_COLORS[entry.stage] ?? DEFAULT_STAGE_COLOR}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Per-requisition table */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Active Requisitions</CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              Click any row to view its pipeline board
            </p>
          </div>
          <Link
            href="/requisitions"
            className="flex items-center gap-1 text-sm text-muted-foreground hover:text-primary transition-colors"
          >
            All requisitions
            <ArrowUpRight className="h-3.5 w-3.5" />
          </Link>
        </CardHeader>
        <CardContent>
          {requisitions.length === 0 ? (
            <div className="py-12 text-center text-sm text-muted-foreground">
              No open requisitions at the moment.{' '}
              <Link href="/requisitions/new" className="text-primary hover:underline">
                Create one
              </Link>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 pr-4 font-medium text-muted-foreground">
                      Requisition
                    </th>
                    <th className="text-left py-2 pr-4 font-medium text-muted-foreground">
                      Department
                    </th>
                    <th className="text-left py-2 pr-4 font-medium text-muted-foreground">
                      Recruiter
                    </th>
                    <th className="text-left py-2 pr-4 font-medium text-muted-foreground">
                      Headcount
                    </th>
                    <th className="text-left py-2 pr-4 font-medium text-muted-foreground">
                      Days Open
                    </th>
                    <th className="text-left py-2 font-medium text-muted-foreground">Pipeline</th>
                  </tr>
                </thead>
                <tbody>
                  {requisitions.map((req) => {
                    const days = getDaysOpen(req.opened_at, req.created_at)
                    const daysClass =
                      days > 60
                        ? 'text-red-600 font-semibold'
                        : days > 30
                          ? 'text-yellow-600'
                          : 'text-muted-foreground'

                    return (
                      <tr
                        key={req.id}
                        className="border-b last:border-0 hover:bg-muted/50 transition-colors"
                      >
                        <td className="py-3 pr-4">
                          <Link
                            href={`/requisitions/${req.id}`}
                            className="font-medium hover:text-primary transition-colors"
                          >
                            {req.title}
                          </Link>
                          <p className="text-xs text-muted-foreground">{req.requisition_id}</p>
                        </td>
                        <td className="py-3 pr-4 text-muted-foreground">
                          {req.department?.name}
                        </td>
                        <td className="py-3 pr-4 text-muted-foreground">
                          {req.recruiter?.user?.first_name} {req.recruiter?.user?.last_name}
                        </td>
                        <td className="py-3 pr-4 w-36">
                          <HeadcountBar filled={req.filled_count} total={req.headcount} />
                        </td>
                        <td className={`py-3 pr-4 tabular-nums ${daysClass}`}>{days}d</td>
                        <td className="py-3">
                          <Link
                            href={`/requisitions/${req.id}/pipeline`}
                            className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
                          >
                            <ExternalLink className="h-3 w-3" />
                            View Board
                          </Link>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

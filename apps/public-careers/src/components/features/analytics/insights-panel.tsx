import Link from 'next/link'
import type { Insight } from '@/types/api'

interface InsightsPanelProps {
  insights: Insight[]
}

const iconsByType = {
  success: (
    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  warning: (
    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
  ),
  info: (
    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  tip: (
    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
    </svg>
  ),
}

const colorsByType = {
  success: {
    bg: 'bg-green-50 border-green-200',
    text: 'text-green-800',
    icon: 'text-green-600',
    button: 'bg-green-600 hover:bg-green-700 text-white',
  },
  warning: {
    bg: 'bg-yellow-50 border-yellow-200',
    text: 'text-yellow-800',
    icon: 'text-yellow-600',
    button: 'bg-yellow-600 hover:bg-yellow-700 text-white',
  },
  info: {
    bg: 'bg-blue-50 border-blue-200',
    text: 'text-blue-800',
    icon: 'text-blue-600',
    button: 'bg-blue-600 hover:bg-blue-700 text-white',
  },
  tip: {
    bg: 'bg-purple-50 border-purple-200',
    text: 'text-purple-800',
    icon: 'text-purple-600',
    button: 'bg-purple-600 hover:bg-purple-700 text-white',
  },
}

export function InsightsPanel({ insights }: InsightsPanelProps) {
  if (insights.length === 0) {
    return null
  }

  return (
    <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
      <div className="flex items-center gap-2 mb-5">
        <svg className="h-5 w-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        <h2 className="text-lg font-semibold">Insights & Recommendations</h2>
      </div>

      <div className="space-y-3">
        {insights.map((insight, index) => {
          const colors = colorsByType[insight.type]
          const icon = iconsByType[insight.type]

          return (
            <div
              key={index}
              className={`rounded-lg border p-4 ${colors.bg}`}
            >
              <div className="flex items-start gap-3">
                <div className={`shrink-0 ${colors.icon}`}>
                  {icon}
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className={`font-semibold text-sm ${colors.text}`}>
                    {insight.title}
                  </h3>
                  <p className={`text-sm mt-1 ${colors.text}`}>
                    {insight.message}
                  </p>
                  {insight.action && insight.action_link && (
                    <Link
                      href={insight.action_link}
                      className={`inline-flex items-center gap-2 mt-3 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${colors.button}`}
                    >
                      {insight.action}
                      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </Link>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

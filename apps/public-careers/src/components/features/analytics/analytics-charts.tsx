'use client'

import type { TimelineDataPoint } from '@/types/api'

interface AnalyticsChartsProps {
  timeline: TimelineDataPoint[]
}

export function AnalyticsCharts({ timeline }: AnalyticsChartsProps) {
  if (timeline.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        <p>No data available</p>
      </div>
    )
  }

  const maxApplications = Math.max(...timeline.map(d => d.applications), 1)

  return (
    <div className="space-y-4">
      {/* Simple bar chart */}
      <div className="flex items-end justify-between gap-2 h-48">
        {timeline.map((data, index) => {
          const height = (data.applications / maxApplications) * 100
          return (
            <div key={index} className="flex flex-col items-center flex-1 gap-2">
              <div className="flex-1 flex items-end w-full">
                <div
                  className="w-full bg-primary rounded-t transition-all hover:bg-primary/80 relative group"
                  style={{ height: `${height}%`, minHeight: data.applications > 0 ? '4px' : '0' }}
                >
                  <div className="absolute -top-6 left-1/2 transform -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <span className="bg-foreground text-background text-xs px-2 py-1 rounded whitespace-nowrap">
                      {data.applications} app{data.applications !== 1 ? 's' : ''}
                    </span>
                  </div>
                </div>
              </div>
              <span className="text-xs text-muted-foreground truncate max-w-full">
                {data.month}
              </span>
            </div>
          )
        })}
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-2 pt-4 border-t border-border">
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded bg-primary" />
          <span className="text-xs text-muted-foreground">Applications per month</span>
        </div>
      </div>
    </div>
  )
}

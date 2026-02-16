import Link from 'next/link'
import type { RecommendedJob } from '@/types/api'

interface RecommendedJobsProps {
  recommendations: RecommendedJob[]
}

export function RecommendedJobs({ recommendations }: RecommendedJobsProps) {
  if (recommendations.length === 0) {
    return null
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-50 border-green-200'
    if (score >= 60) return 'text-blue-600 bg-blue-50 border-blue-200'
    if (score >= 40) return 'text-yellow-600 bg-yellow-50 border-yellow-200'
    return 'text-orange-600 bg-orange-50 border-orange-200'
  }

  const getScoreLabel = (score: number) => {
    if (score >= 80) return 'Excellent Match'
    if (score >= 60) return 'Good Match'
    if (score >= 40) return 'Decent Match'
    return 'Possible Match'
  }

  const formatRemotePolicy = (policy: string): string => {
    const labels: Record<string, string> = {
      onsite: 'On-site',
      remote: 'Remote',
      hybrid: 'Hybrid',
    }
    return labels[policy] ?? policy
  }

  return (
    <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
      <div className="flex items-center gap-2 mb-5">
        <svg className="h-5 w-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
        <h2 className="text-lg font-semibold">Recommended for You</h2>
      </div>

      <p className="text-sm text-muted-foreground mb-5">
        Based on your profile, skills, and preferences
      </p>

      <div className="space-y-4">
        {recommendations.map((job) => (
          <Link
            key={job.id}
            href={`/jobs/${job.slug}`}
            className="group block rounded-lg border border-border bg-background p-4 transition-all hover:border-primary/50 hover:shadow-md"
          >
            <div className="flex items-start gap-4">
              {/* Match Score Badge */}
              <div className="shrink-0">
                <div className={`flex h-14 w-14 flex-col items-center justify-center rounded-lg border-2 ${getScoreColor(job.match_score)}`}>
                  <div className="text-lg font-bold">{job.match_score}%</div>
                  <div className="text-[9px] font-medium">Match</div>
                </div>
              </div>

              {/* Job Details */}
              <div className="flex-1 min-w-0">
                <h3 className="font-semibold text-foreground group-hover:text-primary transition-colors">
                  {job.title}
                </h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  {job.department} • {job.location_city || job.location_name}
                </p>

                {/* Match Reasons */}
                {job.match_reasons.length > 0 && (
                  <div className="mt-3 space-y-1.5">
                    {job.match_reasons.slice(0, 2).map((reason, idx) => (
                      <div key={idx} className="flex items-start gap-2 text-xs text-muted-foreground">
                        <svg className="h-3.5 w-3.5 shrink-0 text-green-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span>{reason}</span>
                      </div>
                    ))}
                    {job.match_reasons.length > 2 && (
                      <div className="text-xs text-muted-foreground pl-5.5">
                        +{job.match_reasons.length - 2} more reasons
                      </div>
                    )}
                  </div>
                )}

                {/* Job Tags */}
                <div className="mt-3 flex flex-wrap gap-2">
                  <span className="inline-flex items-center gap-1 rounded-md bg-muted px-2 py-0.5 text-xs">
                    {job.employment_type.replace('_', '-')}
                  </span>
                  <span className="inline-flex items-center gap-1 rounded-md bg-muted px-2 py-0.5 text-xs">
                    {formatRemotePolicy(job.remote_policy)}
                  </span>
                  {job.level && (
                    <span className="inline-flex items-center gap-1 rounded-md bg-primary/10 px-2 py-0.5 text-xs text-primary">
                      {job.level}
                    </span>
                  )}
                </div>
              </div>

              {/* Arrow Icon */}
              <svg className="h-5 w-5 shrink-0 text-muted-foreground group-hover:text-primary transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </Link>
        ))}
      </div>

      {recommendations.length >= 5 && (
        <div className="mt-5 pt-5 border-t border-border">
          <Link
            href="/jobs"
            className="inline-flex items-center gap-2 text-sm font-medium text-primary hover:text-primary/80 transition-colors"
          >
            View all job openings
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </Link>
        </div>
      )}
    </div>
  )
}

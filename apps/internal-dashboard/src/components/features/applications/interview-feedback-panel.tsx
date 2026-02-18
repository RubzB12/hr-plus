import Link from 'next/link'
import { Calendar, Star, Users, AlertTriangle, ArrowRight, CheckCircle2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface Scorecard {
  id: string
  interviewer_name: string
  overall_rating: number | null
  recommendation: string | null
  is_draft: boolean
  submitted_at: string | null
}

interface Participant {
  id: string
  interviewer: { user_name: string }
  role: string
}

interface Interview {
  id: string
  type: string
  status: string
  scheduled_start: string
  stage_name?: string
  participants?: Participant[]
  scorecards?: Scorecard[]
  scorecard_count?: number
  participant_count?: number
}

const statusVariant: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  scheduled: 'outline',
  confirmed: 'secondary',
  in_progress: 'default',
  completed: 'default',
  cancelled: 'destructive',
  no_show: 'destructive',
}

const recommendationConfig: Record<string, { label: string; className: string }> = {
  strong_hire: { label: 'Strong Hire', className: 'bg-green-100 text-green-700' },
  hire: { label: 'Hire', className: 'bg-green-50 text-green-600' },
  no_hire: { label: 'No Hire', className: 'bg-red-50 text-red-600' },
  strong_no_hire: { label: 'Strong No Hire', className: 'bg-red-100 text-red-700' },
}

function StarRating({ rating }: { rating: number | null }) {
  if (!rating) return <span className="text-xs text-muted-foreground">Not rated</span>
  return (
    <div className="flex gap-0.5">
      {Array.from({ length: 5 }, (_, i) => (
        <Star
          key={i}
          className={`h-3.5 w-3.5 ${i < rating ? 'fill-yellow-400 text-yellow-400' : 'text-muted'}`}
        />
      ))}
    </div>
  )
}

function ConsensusRow({ interviews }: { interviews: Interview[] }) {
  const allScorecards = interviews.flatMap((iv) => iv.scorecards ?? [])
  const submitted = allScorecards.filter((s) => !s.is_draft && s.recommendation)

  if (submitted.length === 0) return null

  const tally: Record<string, number> = {}
  for (const s of submitted) {
    if (s.recommendation) {
      tally[s.recommendation] = (tally[s.recommendation] ?? 0) + 1
    }
  }

  const hireVotes = (tally['strong_hire'] ?? 0) + (tally['hire'] ?? 0)
  const noHireVotes = (tally['no_hire'] ?? 0) + (tally['strong_no_hire'] ?? 0)
  const total = submitted.length

  return (
    <div className="mt-4 pt-4 border-t">
      <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-3">
        Hiring Consensus ({total} evaluator{total !== 1 ? 's' : ''})
      </p>
      <div className="flex items-center gap-3">
        <div className="flex-1 h-2 rounded-full bg-muted overflow-hidden flex">
          {hireVotes > 0 && (
            <div
              className="h-full bg-green-500 transition-all"
              style={{ width: `${(hireVotes / total) * 100}%` }}
            />
          )}
          {noHireVotes > 0 && (
            <div
              className="h-full bg-red-400 transition-all"
              style={{ width: `${(noHireVotes / total) * 100}%` }}
            />
          )}
        </div>
        <div className="flex gap-3 text-xs">
          <span className="flex items-center gap-1 text-green-600 font-medium">
            <CheckCircle2 className="h-3 w-3" />
            {hireVotes} hire
          </span>
          <span className="flex items-center gap-1 text-red-600 font-medium">
            {noHireVotes} no hire
          </span>
        </div>
      </div>
      <div className="flex flex-wrap gap-1.5 mt-2">
        {Object.entries(tally).map(([rec, count]) => {
          const config = recommendationConfig[rec]
          if (!config) return null
          return (
            <span
              key={rec}
              className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${config.className}`}
            >
              {count}× {config.label}
            </span>
          )
        })}
      </div>
    </div>
  )
}

interface InterviewFeedbackPanelProps {
  interviews: Interview[]
}

export function InterviewFeedbackPanel({ interviews }: InterviewFeedbackPanelProps) {
  if (interviews.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            Interview Feedback
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground py-4 text-center">
            No interviews scheduled yet.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calendar className="h-4 w-4" />
          Interview Feedback
          <Badge variant="secondary" className="ml-1">
            {interviews.length}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {interviews.map((interview) => {
          const scorecards = interview.scorecards ?? []
          const submitted = scorecards.filter((s) => !s.is_draft)
          const participantCount = interview.participant_count ?? interview.participants?.length ?? 0
          const missingCount = participantCount - submitted.length
          const isCompleted = interview.status === 'completed'

          return (
            <div key={interview.id} className="rounded-lg border p-4 space-y-3">
              {/* Interview header */}
              <div className="flex items-start justify-between gap-2">
                <div className="space-y-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="text-sm font-medium capitalize">
                      {interview.type.replace(/_/g, ' ')} Interview
                    </p>
                    <Badge variant={statusVariant[interview.status] ?? 'secondary'}>
                      {interview.status.replace(/_/g, ' ')}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {new Date(interview.scheduled_start).toLocaleString('en-US', {
                      dateStyle: 'medium',
                      timeStyle: 'short',
                    })}
                    {interview.stage_name ? ` · ${interview.stage_name}` : ''}
                  </p>
                  {participantCount > 0 && (
                    <p className="text-xs text-muted-foreground flex items-center gap-1">
                      <Users className="h-3 w-3" />
                      {participantCount} interviewer{participantCount !== 1 ? 's' : ''}
                    </p>
                  )}
                </div>
                <Link
                  href={`/interviews/${interview.id}`}
                  className="flex items-center gap-1 text-xs text-primary hover:underline shrink-0"
                >
                  View
                  <ArrowRight className="h-3 w-3" />
                </Link>
              </div>

              {/* Scorecards */}
              {isCompleted && (
                <>
                  {missingCount > 0 && (
                    <div className="flex items-center gap-2 rounded-md bg-yellow-50 border border-yellow-200 px-3 py-2">
                      <AlertTriangle className="h-3.5 w-3.5 text-yellow-600 shrink-0" />
                      <p className="text-xs text-yellow-700">
                        {missingCount} scorecard{missingCount !== 1 ? 's' : ''} still pending
                      </p>
                    </div>
                  )}

                  {submitted.length > 0 ? (
                    <div className="space-y-2">
                      {submitted.map((scorecard) => {
                        const recConfig = scorecard.recommendation
                          ? recommendationConfig[scorecard.recommendation]
                          : null

                        return (
                          <div
                            key={scorecard.id}
                            className="flex items-center justify-between rounded-md bg-muted/50 px-3 py-2"
                          >
                            <div className="space-y-0.5">
                              <p className="text-xs font-medium">{scorecard.interviewer_name}</p>
                              <StarRating rating={scorecard.overall_rating} />
                            </div>
                            {recConfig && (
                              <span
                                className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${recConfig.className}`}
                              >
                                {recConfig.label}
                              </span>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground">
                      No scorecards submitted yet.{' '}
                      <Link href={`/interviews/${interview.id}`} className="text-primary hover:underline">
                        Submit yours
                      </Link>
                    </p>
                  )}
                </>
              )}

              {!isCompleted && interview.status !== 'cancelled' && (
                <p className="text-xs text-muted-foreground">
                  Scorecards will be available after the interview is completed.
                </p>
              )}
            </div>
          )
        })}

        {/* Consensus across all interviews */}
        <ConsensusRow interviews={interviews} />
      </CardContent>
    </Card>
  )
}

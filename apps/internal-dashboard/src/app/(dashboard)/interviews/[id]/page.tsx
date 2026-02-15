import { notFound } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, Calendar, Clock, MapPin, Video, User, FileText, AlertCircle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { getInterviewDetail, getInterviewScorecards } from '@/lib/dal'
import { ScorecardForm } from '@/components/features/interviews/scorecard-form'
import { InterviewActions } from '@/components/features/interviews/interview-actions'

export const metadata = {
  title: 'Interview Details — HR-Plus',
}

interface InterviewDetailPageProps {
  params: Promise<{ id: string }>
}

const statusVariant: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  scheduled: 'outline',
  confirmed: 'secondary',
  in_progress: 'default',
  completed: 'default',
  cancelled: 'destructive',
  rescheduled: 'secondary',
  no_show: 'destructive',
}

const recommendationColors: Record<string, string> = {
  strong_hire: 'text-green-700 bg-green-100',
  hire: 'text-green-600 bg-green-50',
  no_hire: 'text-red-600 bg-red-50',
  strong_no_hire: 'text-red-700 bg-red-100',
}

function formatDateTime(dateString: string) {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('en-US', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

export default async function InterviewDetailPage({ params }: InterviewDetailPageProps) {
  const { id } = await params

  let interview: any
  let scorecardsData: any

  try {
    ;[interview, scorecardsData] = await Promise.all([
      getInterviewDetail(id),
      getInterviewScorecards(id),
    ])
  } catch (error) {
    notFound()
  }

  const isCompleted = interview.status === 'completed'
  const isCancelled = interview.status === 'cancelled'
  const isPast = new Date(interview.scheduled_start) < new Date()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" asChild>
          <Link href="/interviews" className="flex items-center gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back to Interviews
          </Link>
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold tracking-tight">Interview Details</h1>
            <Badge variant={statusVariant[interview.status] ?? 'secondary'}>
              {interview.status.replace('_', ' ').toUpperCase()}
            </Badge>
          </div>
          <p className="text-muted-foreground mt-2">
            {interview.candidate_name} • {interview.requisition_title}
          </p>
        </div>
        {!isCancelled && !isCompleted && (
          <InterviewActions interviewId={id} status={interview.status} />
        )}
      </div>

      {/* Interview Information */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Interview Details
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Type</p>
              <p className="text-sm">{interview.type.replace('_', ' ').toUpperCase()}</p>
            </div>

            <div>
              <p className="text-sm font-medium text-muted-foreground">Scheduled Time</p>
              <div className="flex items-center gap-2 text-sm">
                <Clock className="h-4 w-4" />
                {formatDateTime(interview.scheduled_start)} - {new Date(interview.scheduled_end).toLocaleTimeString('en-US', { timeStyle: 'short' })}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {interview.timezone}
              </p>
            </div>

            {interview.location && (
              <div>
                <p className="text-sm font-medium text-muted-foreground">Location</p>
                <div className="flex items-center gap-2 text-sm">
                  <MapPin className="h-4 w-4" />
                  {interview.location}
                </div>
              </div>
            )}

            {interview.video_link && (
              <div>
                <p className="text-sm font-medium text-muted-foreground">Video Conference</p>
                <div className="flex items-center gap-2 text-sm">
                  <Video className="h-4 w-4" />
                  <a
                    href={interview.video_link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                  >
                    Join Meeting
                  </a>
                </div>
              </div>
            )}

            {interview.stage_name && (
              <div>
                <p className="text-sm font-medium text-muted-foreground">Pipeline Stage</p>
                <p className="text-sm">{interview.stage_name}</p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              Participants
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <p className="text-sm font-medium text-muted-foreground mb-2">Candidate</p>
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                  <User className="h-4 w-4 text-primary" />
                </div>
                <div>
                  <p className="text-sm font-medium">{interview.candidate_name}</p>
                  <p className="text-xs text-muted-foreground">{interview.candidate_email}</p>
                </div>
              </div>
            </div>

            <div>
              <p className="text-sm font-medium text-muted-foreground mb-2">
                Interviewers ({interview.participants?.length || 0})
              </p>
              <div className="space-y-2">
                {interview.participants?.map((participant: any) => (
                  <div key={participant.id} className="flex items-center gap-2">
                    <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center">
                      <span className="text-xs font-medium">
                        {participant.interviewer.user_name.charAt(0)}
                      </span>
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium">{participant.interviewer.user_name}</p>
                      <p className="text-xs text-muted-foreground">
                        {participant.role.replace('_', ' ')} • {participant.rsvp_status}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Preparation Notes */}
      {(interview.prep_notes_interviewer || interview.prep_notes_candidate) && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Preparation Notes
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {interview.prep_notes_interviewer && (
              <div>
                <p className="text-sm font-medium text-muted-foreground mb-2">
                  For Interviewers
                </p>
                <p className="text-sm whitespace-pre-wrap bg-muted p-3 rounded-md">
                  {interview.prep_notes_interviewer}
                </p>
              </div>
            )}

            {interview.prep_notes_candidate && (
              <div>
                <p className="text-sm font-medium text-muted-foreground mb-2">
                  For Candidate
                </p>
                <p className="text-sm whitespace-pre-wrap bg-muted p-3 rounded-md">
                  {interview.prep_notes_candidate}
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Scorecard Section */}
      {(isCompleted || isPast) && (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Submit Your Scorecard</CardTitle>
            </CardHeader>
            <CardContent>
              <ScorecardForm interviewId={id} />
            </CardContent>
          </Card>

          {/* Submitted Scorecards */}
          {scorecardsData.restricted ? (
            <Card>
              <CardContent className="py-12 text-center">
                <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">Submit Your Scorecard First</h3>
                <p className="text-sm text-muted-foreground">
                  To prevent bias, you must submit your own evaluation before viewing other
                  interviewers' scorecards.
                </p>
              </CardContent>
            </Card>
          ) : scorecardsData.scorecards.length > 0 ? (
            <div className="space-y-4">
              <h2 className="text-xl font-semibold">Submitted Scorecards ({scorecardsData.scorecards.length})</h2>
              <div className="grid gap-4">
                {scorecardsData.scorecards.map((scorecard: any) => (
                  <Card key={scorecard.id}>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle className="text-base">{scorecard.interviewer_name}</CardTitle>
                          <p className="text-xs text-muted-foreground">
                            Submitted {new Date(scorecard.submitted_at).toLocaleDateString()}
                          </p>
                        </div>
                        {scorecard.recommendation && (
                          <Badge
                            className={recommendationColors[scorecard.recommendation] || ''}
                          >
                            {scorecard.recommendation.replace('_', ' ').toUpperCase()}
                          </Badge>
                        )}
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {scorecard.overall_rating && (
                        <div>
                          <p className="text-sm font-medium text-muted-foreground mb-1">
                            Overall Rating
                          </p>
                          <div className="flex gap-1">
                            {Array.from({ length: 5 }, (_, i) => (
                              <span
                                key={i}
                                className={`text-lg ${
                                  i < scorecard.overall_rating
                                    ? 'text-yellow-500'
                                    : 'text-gray-300'
                                }`}
                              >
                                ★
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {scorecard.strengths && (
                        <div>
                          <p className="text-sm font-medium text-muted-foreground mb-1">
                            Strengths
                          </p>
                          <p className="text-sm whitespace-pre-wrap">{scorecard.strengths}</p>
                        </div>
                      )}

                      {scorecard.concerns && (
                        <div>
                          <p className="text-sm font-medium text-muted-foreground mb-1">
                            Concerns
                          </p>
                          <p className="text-sm whitespace-pre-wrap">{scorecard.concerns}</p>
                        </div>
                      )}

                      {scorecard.notes && (
                        <div>
                          <p className="text-sm font-medium text-muted-foreground mb-1">
                            Additional Notes
                          </p>
                          <p className="text-sm whitespace-pre-wrap">{scorecard.notes}</p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          ) : null}
        </>
      )}

      {/* Cancellation Info */}
      {isCancelled && interview.cancellation_reason && (
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Cancellation Details</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">
              Cancelled on {new Date(interview.cancelled_at).toLocaleString()}
            </p>
            <p className="text-sm mt-2 whitespace-pre-wrap bg-muted p-3 rounded-md">
              {interview.cancellation_reason}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

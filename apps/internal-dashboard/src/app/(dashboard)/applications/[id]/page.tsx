import { notFound } from 'next/navigation'
import Link from 'next/link'
import { FileText } from 'lucide-react'
import { getApplicationDetail, getInterviews, getPipelineBoard } from '@/lib/dal'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { PipelineProgressStepper } from '@/components/features/applications/pipeline-progress'
import { InterviewFeedbackPanel } from '@/components/features/applications/interview-feedback-panel'
import { ApplicationActionsPanel } from '@/components/features/applications/application-actions-panel'
import { ScoreBreakdown } from '@/components/features/applications/score-breakdown'
import { RescoreButton } from '@/components/features/applications/rescore-button'
import { rescoreApplicationAction } from './actions'
import type { CandidateScore } from '@/types/scoring'

export const metadata = {
  title: 'Application Detail — HR-Plus',
}

interface ApplicationEvent {
  id: string
  event_type: string
  actor_name: string
  from_stage_name: string | null
  to_stage_name: string | null
  metadata: Record<string, unknown>
  created_at: string
}

interface ApplicationNote {
  id: string
  author: { first_name: string; last_name: string; email: string }
  body: string
  is_private: boolean
  created_at: string
}

interface ApplicationTag {
  id: string
  name: string
  color: string
}

interface ApplicationDetail {
  id: string
  application_id: string
  candidate_name: string
  candidate_email: string
  candidate_resume_file: string | null
  requisition_title: string
  requisition_id: string
  requisition_id_display: string
  department: string
  status: string
  current_stage_name: string | null
  source: string
  cover_letter: string
  screening_responses: Record<string, unknown>
  resume_snapshot: Record<string, unknown> | null
  is_starred: boolean
  rejection_reason: string | null
  rejected_at: string | null
  hired_at: string | null
  withdrawn_at: string | null
  applied_at: string
  events: ApplicationEvent[]
  notes: ApplicationNote[]
  tags: ApplicationTag[]
  candidate_score: CandidateScore | null
}

const statusVariant: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  applied: 'default',
  screening: 'outline',
  interview: 'outline',
  offer: 'default',
  hired: 'secondary',
  rejected: 'destructive',
  withdrawn: 'secondary',
}

const statusLabel: Record<string, string> = {
  applied: 'Applied',
  screening: 'Screening',
  interview: 'Interview',
  offer: 'Offer',
  hired: 'Hired',
  rejected: 'Rejected',
  withdrawn: 'Withdrawn',
}

function formatEventType(eventType: string): string {
  return eventType.replace(/[_.]/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

export default async function ApplicationDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  let application: ApplicationDetail
  let interviews: any[] = []

  let stages: { id: string; name: string; order: number; stage_type: string }[] = []

  try {
    const [appData, interviewData] = await Promise.all([
      getApplicationDetail(id),
      getInterviews({ application: id }).catch(() => ({ results: [] })),
    ])
    application = appData
    interviews = interviewData?.results ?? []
  } catch {
    notFound()
  }

  // Fetch pipeline stages so the actions panel can offer "Move Stage"
  if (application.requisition_id) {
    try {
      const pipeline = await getPipelineBoard(application.requisition_id)
      stages = (pipeline?.stages ?? pipeline ?? []).map(
        (s: { id: string; name: string; order: number; stage_type: string }) => ({
          id: s.id,
          name: s.name,
          order: s.order,
          stage_type: s.stage_type,
        }),
      )
    } catch {
      // Non-fatal: actions panel will hide "Move Stage" when stages is empty
    }
  }

  const sortedEvents = [...application.events].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-bold">{application.candidate_name}</h2>
            <Badge variant={statusVariant[application.status] ?? 'secondary'}>
              {statusLabel[application.status] ?? application.status}
            </Badge>
            {application.candidate_resume_file && (
              <Button asChild variant="outline" size="sm">
                <a href={application.candidate_resume_file} target="_blank" rel="noopener noreferrer">
                  <FileText className="h-4 w-4 mr-1.5" />
                  View CV
                </a>
              </Button>
            )}
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            {application.application_id} &middot; {application.candidate_email}
          </p>
        </div>
        <ApplicationActionsPanel
          applicationId={application.id}
          isStarred={application.is_starred}
          currentStageName={application.current_stage_name}
          stages={stages}
          status={application.status}
          candidateName={application.candidate_name}
        />
      </div>

      {/* Pipeline Progress */}
      <PipelineProgressStepper
        currentStatus={application.status}
        rejectedAt={application.rejected_at}
        withdrawnAt={application.withdrawn_at}
      />

      {/* Score Breakdown */}
      {application.candidate_score ? (
        <ScoreBreakdown score={application.candidate_score} />
      ) : (
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">Candidate Score</CardTitle>
              <RescoreButton
                applicationId={application.id}
                action={rescoreApplicationAction}
              />
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              No score computed yet. Click &ldquo;Compute Score&rdquo; to score this application
              against the requisition criteria.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Info Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Requisition</CardTitle>
          </CardHeader>
          <CardContent>
            {application.requisition_id ? (
              <Link
                href={`/requisitions/${application.requisition_id}`}
                className="font-medium hover:underline text-primary"
              >
                {application.requisition_title}
              </Link>
            ) : (
              <p className="font-medium">{application.requisition_title}</p>
            )}
            <p className="text-sm text-muted-foreground">{application.requisition_id_display}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Department</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-medium">{application.department}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Stage</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-medium">{application.current_stage_name ?? 'No stage'}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Source</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-medium capitalize">{application.source}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Applied Date</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-medium">{new Date(application.applied_at).toLocaleDateString()}</p>
          </CardContent>
        </Card>
        {application.rejection_reason && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Rejection Reason</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="font-medium">{application.rejection_reason}</p>
              {application.rejected_at && (
                <p className="text-sm text-muted-foreground">
                  {new Date(application.rejected_at).toLocaleDateString()}
                </p>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Tags */}
      {application.tags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {application.tags.map((tag) => (
            <Badge key={tag.id} variant="outline" style={{ borderColor: tag.color, color: tag.color }}>
              {tag.name}
            </Badge>
          ))}
        </div>
      )}

      {/* Cover Letter */}
      {application.cover_letter && (
        <Card>
          <CardHeader>
            <CardTitle>Cover Letter</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose prose-sm max-w-none dark:prose-invert whitespace-pre-wrap">
              {application.cover_letter}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Event Timeline */}
      {sortedEvents.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Event Timeline</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {sortedEvents.map((event) => (
                <div key={event.id}>
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-medium text-sm">{formatEventType(event.event_type)}</p>
                      <p className="text-xs text-muted-foreground">by {event.actor_name}</p>
                      {event.from_stage_name && event.to_stage_name && (
                        <p className="text-xs text-muted-foreground">
                          {event.from_stage_name} &rarr; {event.to_stage_name}
                        </p>
                      )}
                    </div>
                    <span className="text-xs text-muted-foreground whitespace-nowrap">
                      {new Date(event.created_at).toLocaleString()}
                    </span>
                  </div>
                  <Separator className="mt-4" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Interview Feedback */}
      <InterviewFeedbackPanel interviews={interviews} />

      {/* Notes */}
      {application.notes.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Notes</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {application.notes.map((note) => (
                <div key={note.id}>
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-sm">
                      {note.author.first_name} {note.author.last_name}
                    </p>
                    {note.is_private && (
                      <Badge variant="outline" className="text-xs">Private</Badge>
                    )}
                    <span className="text-xs text-muted-foreground">
                      {new Date(note.created_at).toLocaleString()}
                    </span>
                  </div>
                  <p className="mt-1 text-sm whitespace-pre-wrap">{note.body}</p>
                  <Separator className="mt-4" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

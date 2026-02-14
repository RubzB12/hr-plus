import { notFound } from 'next/navigation'
import { getApplicationDetail } from '@/lib/dal'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'

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
  requisition_title: string
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

  try {
    application = await getApplicationDetail(id)
  } catch {
    notFound()
  }

  const sortedEvents = [...application.events].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3">
          <h2 className="text-2xl font-bold">{application.candidate_name}</h2>
          <Badge variant={statusVariant[application.status] ?? 'secondary'}>
            {statusLabel[application.status] ?? application.status}
          </Badge>
          {application.is_starred && (
            <span className="text-yellow-500" title="Starred">&#9733;</span>
          )}
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          {application.application_id} &middot; {application.candidate_email}
        </p>
      </div>

      {/* Info Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Requisition</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-medium">{application.requisition_title}</p>
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

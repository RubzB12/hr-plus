import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { getApplicationDetail } from '@/lib/dal'
import type { CandidateApplicationDetail, ApplicationEvent } from '@/types/api'
import { WithdrawButton } from './withdraw-button'

export const metadata: Metadata = {
  title: 'Application Detail',
}

interface ApplicationDetailPageProps {
  params: Promise<{ id: string }>
}

const statusStyles: Record<string, string> = {
  applied: 'bg-blue-100 text-blue-700',
  screening: 'bg-yellow-100 text-yellow-700',
  interview: 'bg-purple-100 text-purple-700',
  offer: 'bg-green-100 text-green-700',
  hired: 'bg-emerald-100 text-emerald-700',
  rejected: 'bg-red-100 text-red-700',
  withdrawn: 'bg-gray-100 text-gray-600',
}

function StatusBadge({ status }: { status: string }) {
  const style = statusStyles[status] ?? 'bg-gray-100 text-gray-600'
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${style}`}
    >
      {status}
    </span>
  )
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

function formatDateTime(dateStr: string): string {
  return new Date(dateStr).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

function eventLabel(event: ApplicationEvent): string {
  switch (event.event_type) {
    case 'application.created':
      return 'Application submitted'
    case 'application.stage_changed':
      return event.to_stage_name
        ? `Moved to ${event.to_stage_name}`
        : 'Stage changed'
    case 'application.withdrawn':
      return 'Application withdrawn'
    case 'application.rejected':
      return 'Application declined'
    case 'application.offered':
      return 'Offer extended'
    case 'application.hired':
      return 'Hired'
    default:
      return event.event_type.replace(/\./g, ' ').replace(/^./, (c) => c.toUpperCase())
  }
}

const canWithdraw = (status: string) =>
  !['rejected', 'withdrawn', 'hired'].includes(status)

export default async function ApplicationDetailPage({
  params,
}: ApplicationDetailPageProps) {
  const { id } = await params

  let application: CandidateApplicationDetail
  try {
    application = await getApplicationDetail(id)
  } catch {
    notFound()
  }

  const events: ApplicationEvent[] = application.events ?? []

  return (
    <div>
      <Link
        href="/dashboard/applications"
        className="text-sm text-muted-foreground hover:text-foreground"
      >
        &larr; Back to applications
      </Link>

      {/* Header */}
      <div className="mt-4 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">{application.requisition_title}</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {application.department}
            {application.location && <span> &middot; {application.location}</span>}
          </p>
        </div>
        <StatusBadge status={application.status} />
      </div>

      {/* Details grid */}
      <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <div className="rounded-lg border border-border p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Applied on
          </p>
          <p className="mt-1 text-sm font-medium">
            {formatDate(application.applied_at)}
          </p>
        </div>
        <div className="rounded-lg border border-border p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Current stage
          </p>
          <p className="mt-1 text-sm font-medium">
            {application.current_stage_name ?? 'N/A'}
          </p>
        </div>
        <div className="rounded-lg border border-border p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Application ID
          </p>
          <p className="mt-1 text-sm font-mono">
            {application.application_id}
          </p>
        </div>
      </div>

      {/* Cover letter */}
      {application.cover_letter && (
        <div className="mt-8">
          <h2 className="text-lg font-semibold">Cover Letter</h2>
          <div className="mt-3 rounded-lg border border-border bg-muted p-4 text-sm leading-relaxed whitespace-pre-wrap">
            {application.cover_letter}
          </div>
        </div>
      )}

      {/* Screening responses */}
      {application.screening_responses &&
        Object.keys(application.screening_responses).length > 0 && (
          <div className="mt-8">
            <h2 className="text-lg font-semibold">Screening Responses</h2>
            <dl className="mt-3 space-y-3">
              {Object.entries(application.screening_responses).map(
                ([question, answer]) => (
                  <div
                    key={question}
                    className="rounded-lg border border-border p-4"
                  >
                    <dt className="text-sm font-medium">{question}</dt>
                    <dd className="mt-1 text-sm text-muted-foreground">
                      {answer}
                    </dd>
                  </div>
                )
              )}
            </dl>
          </div>
        )}

      {/* Timeline */}
      {events.length > 0 && (
        <div className="mt-8">
          <h2 className="text-lg font-semibold">Activity Timeline</h2>
          <ol className="mt-4 space-y-4">
            {events.map((event) => (
              <li key={event.id} className="flex gap-4">
                <div className="relative flex flex-col items-center">
                  <div className="h-2.5 w-2.5 rounded-full bg-primary" />
                  <div className="flex-1 w-px bg-border" />
                </div>
                <div className="pb-4">
                  <p className="text-sm font-medium">{eventLabel(event)}</p>
                  <p className="text-xs text-muted-foreground">
                    {formatDateTime(event.created_at)}
                  </p>
                </div>
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Withdraw */}
      {canWithdraw(application.status) && (
        <div className="mt-10 rounded-lg border border-border p-6">
          <h2 className="text-sm font-semibold">Withdraw application</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Once withdrawn, you will not be considered for this position. This
            action cannot be undone.
          </p>
          <div className="mt-4">
            <WithdrawButton applicationId={application.id} />
          </div>
        </div>
      )}
    </div>
  )
}

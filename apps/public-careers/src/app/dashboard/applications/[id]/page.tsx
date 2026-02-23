import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { getApplicationDetail } from '@/lib/dal'
import type { CandidateApplicationDetail, ApplicationEvent } from '@/types/api'
import { WithdrawButton } from './withdraw-button'
import { StageDescriptionTooltip } from '@/components/features/applications/stage-description-tooltip'

export const metadata: Metadata = {
  title: 'Application Detail',
}

interface ApplicationDetailPageProps {
  params: Promise<{ id: string }>
}

const statusStyles: Record<string, { bg: string; text: string; border: string }> = {
  applied: { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' },
  screening: { bg: 'bg-yellow-50', text: 'text-yellow-700', border: 'border-yellow-200' },
  interview: { bg: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-200' },
  offer: { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200' },
  hired: { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200' },
  rejected: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' },
  withdrawn: { bg: 'bg-gray-50', text: 'text-gray-600', border: 'border-gray-200' },
}

function StatusBadge({ status }: { status: string }) {
  const style = statusStyles[status] ?? statusStyles.applied
  return (
    <span
      className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold capitalize ${style.bg} ${style.text}`}
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

function eventIcon(eventType: string) {
  switch (eventType) {
    case 'application.created':
      return (
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      )
    case 'application.stage_changed':
      return (
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
        </svg>
      )
    case 'application.offered':
      return (
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )
    case 'application.hired':
      return (
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
        </svg>
      )
    default:
      return (
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      )
  }
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

function stageDurationBadgeClass(days: number): string {
  if (days <= 5) return 'bg-green-100 text-green-700'
  if (days <= 14) return 'bg-yellow-100 text-yellow-700'
  return 'bg-red-100 text-red-700'
}

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
  const statusStyle = statusStyles[application.status] ?? statusStyles.applied

  // Compute days in current stage (from last stage_changed event, or applied_at if none)
  const lastStageChange = events.find(e => e.event_type === 'application.stage_changed')
  const stageSinceDate = lastStageChange?.created_at ?? application.applied_at
  const daysInStage = Math.floor((Date.now() - new Date(stageSinceDate).getTime()) / 86_400_000)

  return (
    <div>
      {/* Back Link */}
      <Link
        href="/dashboard/applications"
        className="inline-flex items-center gap-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
      >
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Back to applications
      </Link>

      {/* Header */}
      <div className="mt-6 flex flex-wrap items-start justify-between gap-4">
        <div className="flex-1">
          <h1 className="text-3xl font-bold tracking-tight">{application.requisition_title}</h1>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
              {application.department}
            </span>
            {application.location && (
              <>
                <span className="text-muted-foreground/50">•</span>
                <span className="flex items-center gap-1">
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  {application.location}
                </span>
              </>
            )}
          </div>
        </div>
        <StatusBadge status={application.status} />
      </div>

      {/* Info Cards */}
      <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
              <svg className="h-5 w-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
              <p className="text-xs font-medium text-muted-foreground">Applied on</p>
              <p className="text-sm font-semibold">{formatDate(application.applied_at)}</p>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <div className={`flex h-10 w-10 items-center justify-center rounded-lg border-2 ${statusStyle.border} ${statusStyle.bg}`}>
              <svg className={`h-5 w-5 ${statusStyle.text}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
            <div>
              <p className="text-xs font-medium text-muted-foreground">Current stage</p>
              <div className="flex items-center gap-1.5">
                <p className="text-sm font-semibold">{application.current_stage_name ?? 'N/A'}</p>
                <StageDescriptionTooltip stageName={application.current_stage_name ?? ''} />
              </div>
              {!['rejected', 'hired', 'withdrawn'].includes(application.status) && (
                <span className={`mt-1 inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${stageDurationBadgeClass(daysInStage)}`}>
                  {daysInStage === 0 ? 'Since today' : daysInStage === 1 ? '1 day in stage' : `${daysInStage} days in stage`}
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gray-500/10">
              <svg className="h-5 w-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
              </svg>
            </div>
            <div>
              <p className="text-xs font-medium text-muted-foreground">Application ID</p>
              <p className="text-xs font-mono font-semibold truncate">{application.application_id}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Cover Letter */}
      {application.cover_letter && (
        <div className="mt-8">
          <div className="flex items-center gap-2 mb-4">
            <svg className="h-5 w-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h2 className="text-lg font-semibold">Cover Letter</h2>
          </div>
          <div className="rounded-xl border border-border bg-muted/50 p-6 text-sm leading-relaxed whitespace-pre-wrap">
            {application.cover_letter}
          </div>
        </div>
      )}

      {/* Screening Responses */}
      {application.screening_responses &&
        Object.keys(application.screening_responses).length > 0 && (
          <div className="mt-8">
            <div className="flex items-center gap-2 mb-4">
              <svg className="h-5 w-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
              </svg>
              <h2 className="text-lg font-semibold">Screening Responses</h2>
            </div>
            <dl className="space-y-3">
              {Object.entries(application.screening_responses).map(
                ([question, answer]) => (
                  <div
                    key={question}
                    className="rounded-xl border border-border bg-card p-5 shadow-sm"
                  >
                    <dt className="text-sm font-semibold text-foreground">{question}</dt>
                    <dd className="mt-2 text-sm text-muted-foreground leading-relaxed">
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
          <div className="flex items-center gap-2 mb-4">
            <svg className="h-5 w-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h2 className="text-lg font-semibold">Activity Timeline</h2>
          </div>
          <ol className="relative border-l-2 border-border pl-6 space-y-6">
            {events.map((event, index) => (
              <li key={event.id} className="relative">
                <div className="absolute -left-[1.6875rem] flex h-8 w-8 items-center justify-center rounded-full border-2 border-border bg-background">
                  <div className="text-primary">
                    {eventIcon(event.event_type)}
                  </div>
                </div>
                <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
                  <p className="font-semibold text-foreground">{eventLabel(event)}</p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {formatDateTime(event.created_at)}
                  </p>
                </div>
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Rejection Feedback */}
      {application.status === 'rejected' && application.rejection_reason && (
        <div className="mt-8 rounded-xl border border-blue-200 bg-blue-50/60 p-6">
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-100">
              <svg className="h-5 w-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="flex-1">
              <h2 className="font-semibold text-blue-900">Recruiter Feedback</h2>
              <p className="mt-0.5 text-xs text-blue-600">This feedback is provided by the hiring team</p>
              <p className="mt-3 text-sm leading-relaxed text-blue-800">{application.rejection_reason}</p>
            </div>
          </div>
        </div>
      )}

      {/* Withdraw Section */}
      {canWithdraw(application.status) && (
        <div className="mt-10 rounded-xl border-2 border-red-200 bg-red-50/50 p-6">
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-red-100">
              <svg className="h-5 w-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div className="flex-1">
              <h2 className="font-semibold text-red-900">Withdraw Application</h2>
              <p className="mt-1 text-sm text-red-700">
                Once withdrawn, you will not be considered for this position. This action cannot be undone.
              </p>
              <div className="mt-4">
                <WithdrawButton applicationId={application.id} />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

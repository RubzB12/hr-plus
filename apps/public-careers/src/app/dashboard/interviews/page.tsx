import type { CandidateInterview } from '@/types/api'
import { getAllInterviews } from '@/lib/dal'
import { confirmInterviewAction } from './actions'

export const dynamic = 'force-dynamic'

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  scheduled: { label: 'Scheduled', color: 'bg-yellow-100 text-yellow-700' },
  confirmed: { label: 'Confirmed', color: 'bg-green-100 text-green-700' },
  in_progress: { label: 'In Progress', color: 'bg-blue-100 text-blue-700' },
  completed: { label: 'Completed', color: 'bg-gray-100 text-gray-600' },
  cancelled: { label: 'Cancelled', color: 'bg-red-100 text-red-600' },
  rescheduled: { label: 'Rescheduled', color: 'bg-orange-100 text-orange-700' },
  no_show: { label: 'No Show', color: 'bg-red-100 text-red-600' },
}

function formatDateTime(start: string, end: string, timezone: string) {
  const startDate = new Date(start)
  const endDate = new Date(end)
  const dateStr = startDate.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
  const startTime = startDate.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
  const endTime = endDate.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
  return `${dateStr} · ${startTime} – ${endTime} ${timezone}`
}

function buildGoogleCalendarLink(interview: CandidateInterview): string {
  const formatForGcal = (dateStr: string) =>
    new Date(dateStr).toISOString().replace(/[-:]/g, '').replace('.000', '')

  const params = new URLSearchParams({
    action: 'TEMPLATE',
    text: `Interview: ${interview.requisition_title}`,
    dates: `${formatForGcal(interview.scheduled_start)}/${formatForGcal(interview.scheduled_end)}`,
    details: interview.prep_notes_candidate
      ? `Prep notes: ${interview.prep_notes_candidate}`
      : `${interview.type_display} interview for ${interview.requisition_title}`,
    location: interview.video_link || interview.location || '',
  })
  return `https://calendar.google.com/calendar/render?${params.toString()}`
}

function isUpcoming(interview: CandidateInterview) {
  return (
    ['scheduled', 'confirmed', 'rescheduled'].includes(interview.status) &&
    new Date(interview.scheduled_start) > new Date()
  )
}

function ConfirmButton({ interviewId }: { interviewId: string }) {
  return (
    <form
      action={async () => {
        'use server'
        await confirmInterviewAction(interviewId)
      }}
    >
      <button
        type="submit"
        className="rounded-lg bg-green-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-green-700"
      >
        Confirm Attendance
      </button>
    </form>
  )
}

function InterviewCard({ interview }: { interview: CandidateInterview }) {
  const status = STATUS_LABELS[interview.status] ?? { label: interview.status, color: 'bg-gray-100 text-gray-600' }
  const upcoming = isUpcoming(interview)

  return (
    <div className={`rounded-xl border bg-white p-5 ${upcoming ? 'border-blue-200' : 'border-gray-200'}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-medium text-gray-500">{interview.type_display}</span>
            <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${status.color}`}>
              {status.label}
            </span>
          </div>
          <h3 className="mt-1 font-semibold text-gray-900">{interview.requisition_title}</h3>
          <p className="mt-1 text-sm text-gray-500">
            {formatDateTime(interview.scheduled_start, interview.scheduled_end, interview.timezone)}
          </p>
          {interview.location && !interview.video_link && (
            <p className="mt-1 text-sm text-gray-500">📍 {interview.location}</p>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {interview.video_link && (
            <a
              href={interview.video_link}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-lg border border-blue-200 bg-blue-50 px-3 py-1.5 text-sm font-medium text-blue-700 hover:bg-blue-100"
            >
              Join Video Call
            </a>
          )}

          {upcoming && (
            <a
              href={buildGoogleCalendarLink(interview)}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-lg border border-gray-200 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Add to Calendar
            </a>
          )}

          {(interview.status === 'scheduled' || interview.status === 'rescheduled') && upcoming && (
            <ConfirmButton interviewId={interview.id} />
          )}
        </div>
      </div>

      {interview.prep_notes_candidate && (
        <div className="mt-4 rounded-lg border border-amber-100 bg-amber-50 p-3">
          <p className="text-xs font-medium text-amber-800">Prep Notes</p>
          <p className="mt-1 text-sm text-amber-700">{interview.prep_notes_candidate}</p>
        </div>
      )}
    </div>
  )
}

export default async function InterviewsPage() {
  let interviews: CandidateInterview[] = []
  try {
    interviews = await getAllInterviews()
  } catch {
    interviews = []
  }

  const upcomingInterviews = interviews.filter(isUpcoming)
  const pastInterviews = interviews.filter(i => !isUpcoming(i))

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Interviews</h1>
        <p className="mt-1 text-sm text-gray-500">
          Manage your upcoming and past interviews.
        </p>
      </div>

      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500">
          Upcoming ({upcomingInterviews.length})
        </h2>
        {upcomingInterviews.length === 0 ? (
          <div className="rounded-xl border border-dashed border-gray-200 bg-white p-10 text-center">
            <p className="text-sm text-gray-500">
              No upcoming interviews. Check back when your applications progress.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {upcomingInterviews.map(interview => (
              <InterviewCard key={interview.id} interview={interview} />
            ))}
          </div>
        )}
      </section>

      {pastInterviews.length > 0 && (
        <section>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500">
            Past ({pastInterviews.length})
          </h2>
          <div className="space-y-3">
            {pastInterviews.map(interview => (
              <InterviewCard key={interview.id} interview={interview} />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}

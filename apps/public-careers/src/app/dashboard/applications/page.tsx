import type { Metadata } from 'next'
import Link from 'next/link'
import { getApplications } from '@/lib/dal'
import type { CandidateApplication, PaginatedResponse } from '@/types/api'

export const metadata: Metadata = {
  title: 'My Applications',
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

export default async function ApplicationsPage() {
  const data: PaginatedResponse<CandidateApplication> | CandidateApplication[] =
    await getApplications()

  const applications: CandidateApplication[] = Array.isArray(data)
    ? data
    : data.results ?? []

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">My Applications</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Track the status of your job applications.
          </p>
        </div>
        <Link
          href="/jobs"
          className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-dark"
        >
          Browse jobs
        </Link>
      </div>

      {applications.length === 0 ? (
        <div className="mt-12 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-muted">
            <svg
              className="h-8 w-8 text-muted-foreground"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m6.75 12-3-3m0 0-3 3m3-3v6m-1.5-15H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z"
              />
            </svg>
          </div>
          <h2 className="text-lg font-semibold">No applications yet</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Start exploring open positions and submit your first application.
          </p>
          <Link
            href="/jobs"
            className="mt-4 inline-block rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-primary-dark"
          >
            Find jobs
          </Link>
        </div>
      ) : (
        <div className="mt-6 space-y-3">
          {applications.map((app) => (
            <Link
              key={app.id}
              href={`/dashboard/applications/${app.id}`}
              className="flex items-center justify-between rounded-lg border border-border p-4 transition-shadow hover:shadow-md"
            >
              <div className="min-w-0 flex-1">
                <p className="font-medium">{app.requisition_title}</p>
                <p className="mt-0.5 text-sm text-muted-foreground">
                  {app.department}
                  {app.current_stage_name && (
                    <span> &middot; {app.current_stage_name}</span>
                  )}
                </p>
              </div>
              <div className="ml-4 flex shrink-0 items-center gap-4">
                <StatusBadge status={app.status} />
                <span className="text-xs text-muted-foreground">
                  {formatDate(app.applied_at)}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

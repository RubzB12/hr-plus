import Link from 'next/link'
import { getSavedJobs } from '@/lib/dal'
import type { SavedJob } from '@/types/api'
import { unsaveJobAction } from './actions'
import { DeadlineBadge } from '@/components/features/jobs/deadline-badge'

export const dynamic = 'force-dynamic'

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

function RemoveButton({ savedJobId }: { savedJobId: string }) {
  return (
    <form
      action={async () => {
        'use server'
        await unsaveJobAction(savedJobId)
      }}
    >
      <button
        type="submit"
        className="text-sm text-gray-400 transition-colors hover:text-red-500"
        title="Remove from saved jobs"
      >
        Remove
      </button>
    </form>
  )
}

export default async function SavedJobsPage() {
  let savedJobs: SavedJob[] = []
  try {
    savedJobs = await getSavedJobs()
  } catch {
    savedJobs = []
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Saved Jobs</h1>
        <p className="mt-1 text-sm text-gray-500">
          Jobs you&apos;ve bookmarked to review or apply to later.
        </p>
      </div>

      {savedJobs.length === 0 ? (
        <div className="rounded-xl border border-dashed border-gray-200 bg-white p-12 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-gray-100">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="h-6 w-6 text-gray-400">
              <path strokeLinecap="round" strokeLinejoin="round" d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.25 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0111.186 0z" />
            </svg>
          </div>
          <h3 className="text-base font-medium text-gray-900">No saved jobs yet</h3>
          <p className="mt-1 text-sm text-gray-500">
            Bookmark jobs while browsing so you can come back to them later.
          </p>
          <Link
            href="/jobs"
            className="mt-4 inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            Browse jobs
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {savedJobs.map((job) => (
            <div
              key={job.id}
              className="flex items-center justify-between rounded-xl border border-gray-200 bg-white px-5 py-4 transition-shadow hover:shadow-sm"
            >
              <div className="min-w-0 flex-1">
                <Link
                  href={`/jobs/${job.requisition_slug}`}
                  className="block font-medium text-gray-900 hover:text-blue-600"
                >
                  {job.requisition_title}
                </Link>
                <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-gray-500">
                  {job.requisition_department && (
                    <span>{job.requisition_department}</span>
                  )}
                  {job.requisition_location && (
                    <>
                      <span className="text-gray-300">·</span>
                      <span>{job.requisition_location}</span>
                    </>
                  )}
                  {job.requisition_employment_type && (
                    <>
                      <span className="text-gray-300">·</span>
                      <span className="capitalize">{job.requisition_employment_type.replace(/_/g, ' ')}</span>
                    </>
                  )}
                </div>
              </div>
              <div className="ml-4 flex shrink-0 items-center gap-4">
                <DeadlineBadge deadline={job.requisition_application_deadline} />
                <span className="text-xs text-gray-400">
                  Saved {formatDate(job.created_at)}
                </span>
                <RemoveButton savedJobId={job.id} />
                <Link
                  href={`/jobs/${job.requisition_slug}`}
                  className="rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
                >
                  View
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

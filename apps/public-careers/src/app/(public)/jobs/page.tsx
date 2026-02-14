import { Suspense } from 'react'
import type { Metadata } from 'next'
import Link from 'next/link'
import { getJobs, getCategories } from '@/lib/dal'
import JobFilters from '@/components/features/job-search/job-filters'
import type { PaginatedResponse, PublicJob, JobCategory } from '@/types/api'

export const metadata: Metadata = {
  title: 'Open Positions',
  description:
    'Browse all open positions at HR-Plus. Filter by department, employment type, and work mode to find your perfect role.',
}

function formatSalary(job: PublicJob): string {
  if (!job.salary_min && !job.salary_max) return ''
  const currency = job.salary_currency ?? 'USD'
  const fmt = (v: string) =>
    new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
      maximumFractionDigits: 0,
    }).format(Number(v))

  if (job.salary_min && job.salary_max)
    return `${fmt(job.salary_min)} - ${fmt(job.salary_max)}`
  if (job.salary_min) return `From ${fmt(job.salary_min)}`
  return `Up to ${fmt(job.salary_max!)}`
}

function formatRemotePolicy(policy: string): string {
  const labels: Record<string, string> = {
    onsite: 'On-site',
    remote: 'Remote',
    hybrid: 'Hybrid',
  }
  return labels[policy] ?? policy
}

function getPageFromUrl(url: string | null): string | null {
  if (!url) return null
  try {
    const parsed = new URL(url)
    return parsed.searchParams.get('page')
  } catch {
    return null
  }
}

interface JobsPageProps {
  searchParams: Promise<{
    search?: string
    department?: string
    employment_type?: string
    remote_policy?: string
    page?: string
  }>
}

async function JobListingsContent({ searchParams }: JobsPageProps) {
  const params = await searchParams

  let jobs: PaginatedResponse<PublicJob> = {
    count: 0,
    next: null,
    previous: null,
    results: [],
  }
  let categories: JobCategory[] = []

  try {
    jobs = await getJobs(params)
  } catch {
    // Graceful degradation
  }

  try {
    categories = await getCategories()
  } catch {
    // Graceful degradation
  }

  const nextPage = getPageFromUrl(jobs.next)
  const prevPage = getPageFromUrl(jobs.previous)

  function buildPageUrl(page: string): string {
    const p = new URLSearchParams()
    if (params.search) p.set('search', params.search)
    if (params.department) p.set('department', params.department)
    if (params.employment_type) p.set('employment_type', params.employment_type)
    if (params.remote_policy) p.set('remote_policy', params.remote_policy)
    p.set('page', page)
    return `/jobs?${p.toString()}`
  }

  return (
    <div className="mx-auto max-w-7xl px-6 py-10">
      {/* Search bar */}
      <form action="/jobs" method="GET" className="flex items-center gap-2">
        <input
          type="text"
          name="search"
          defaultValue={params.search ?? ''}
          placeholder="Search jobs..."
          className="flex-1 rounded-lg border border-border bg-background px-4 py-2.5 text-sm outline-none placeholder:text-muted-foreground focus:ring-2 focus:ring-primary"
        />
        {/* Preserve active filters in hidden fields */}
        {params.department && (
          <input type="hidden" name="department" value={params.department} />
        )}
        {params.employment_type && (
          <input
            type="hidden"
            name="employment_type"
            value={params.employment_type}
          />
        )}
        {params.remote_policy && (
          <input
            type="hidden"
            name="remote_policy"
            value={params.remote_policy}
          />
        )}
        <button
          type="submit"
          className="rounded-lg bg-primary px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-primary-dark"
        >
          Search
        </button>
      </form>

      {/* Filters */}
      <div className="mt-6">
        <JobFilters categories={categories} />
      </div>

      {/* Results count */}
      <p className="mt-6 text-sm text-muted-foreground">
        {jobs.count} {jobs.count === 1 ? 'position' : 'positions'} found
      </p>

      {/* Job cards */}
      {jobs.results.length > 0 ? (
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {jobs.results.map((job) => (
            <Link
              key={job.id}
              href={`/jobs/${job.slug}`}
              className="group rounded-lg border border-border bg-background p-6 transition-shadow hover:shadow-md"
            >
              <h2 className="font-semibold group-hover:text-primary">
                {job.title}
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                {job.department}
              </p>
              <div className="mt-4 flex flex-wrap gap-2 text-xs">
                <span className="rounded-full bg-muted px-2.5 py-1">
                  {job.location_city
                    ? `${job.location_city}, ${job.location_country}`
                    : job.location_name}
                </span>
                <span className="rounded-full bg-muted px-2.5 py-1">
                  {job.employment_type}
                </span>
                <span className="rounded-full bg-muted px-2.5 py-1">
                  {formatRemotePolicy(job.remote_policy)}
                </span>
              </div>
              {(job.salary_min || job.salary_max) && (
                <p className="mt-3 text-sm font-medium text-primary">
                  {formatSalary(job)}
                </p>
              )}
            </Link>
          ))}
        </div>
      ) : (
        <div className="mt-12 text-center">
          <p className="text-lg font-medium">No positions found</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Try adjusting your search or filters.
          </p>
          <Link
            href="/jobs"
            className="mt-4 inline-block text-sm font-medium text-primary hover:text-primary-dark"
          >
            Clear all filters
          </Link>
        </div>
      )}

      {/* Pagination */}
      {(prevPage || nextPage) && (
        <nav
          aria-label="Pagination"
          className="mt-10 flex items-center justify-center gap-4"
        >
          {prevPage ? (
            <Link
              href={buildPageUrl(prevPage)}
              className="rounded-lg border border-border px-4 py-2 text-sm font-medium transition-colors hover:bg-muted"
            >
              &larr; Previous
            </Link>
          ) : (
            <span className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-muted-foreground opacity-50">
              &larr; Previous
            </span>
          )}
          {nextPage ? (
            <Link
              href={buildPageUrl(nextPage)}
              className="rounded-lg border border-border px-4 py-2 text-sm font-medium transition-colors hover:bg-muted"
            >
              Next &rarr;
            </Link>
          ) : (
            <span className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-muted-foreground opacity-50">
              Next &rarr;
            </span>
          )}
        </nav>
      )}
    </div>
  )
}

export default async function JobsPage(props: JobsPageProps) {
  return (
    <>
      <section className="bg-muted py-10">
        <div className="mx-auto max-w-7xl px-6">
          <h1 className="text-3xl font-bold">Open Positions</h1>
          <p className="mt-2 text-muted-foreground">
            Find the role that is right for you.
          </p>
        </div>
      </section>

      <Suspense
        fallback={
          <div className="mx-auto max-w-7xl px-6 py-10">
            <div className="animate-pulse space-y-4">
              <div className="h-10 rounded-lg bg-muted" />
              <div className="h-8 w-48 rounded-lg bg-muted" />
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} className="h-40 rounded-lg bg-muted" />
                ))}
              </div>
            </div>
          </div>
        }
      >
        <JobListingsContent searchParams={props.searchParams} />
      </Suspense>
    </>
  )
}

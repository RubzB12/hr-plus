import { Suspense } from 'react'
import type { Metadata } from 'next'
import Link from 'next/link'
import { getJobs, getCategories, getLocations } from '@/lib/dal'
import JobFilters from '@/components/features/job-search/job-filters'
import ActiveFilters from '@/components/features/job-search/active-filters'
import type { PaginatedResponse, PublicJob, JobCategory } from '@/types/api'

export const metadata: Metadata = {
  title: 'Open Positions - Find Your Dream Job',
  description:
    'Browse all open positions at HR-Plus. Filter by department, location, employment type, and work mode to find your perfect role.',
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
    location?: string
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
  let locations: Array<{ id: string; name: string }> = []

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

  try {
    locations = await getLocations()
  } catch {
    // Graceful degradation
  }

  const nextPage = getPageFromUrl(jobs.next)
  const prevPage = getPageFromUrl(jobs.previous)

  function buildPageUrl(page: string): string {
    const p = new URLSearchParams()
    if (params.search) p.set('search', params.search)
    if (params.department) p.set('department', params.department)
    if (params.location) p.set('location', params.location)
    if (params.employment_type) p.set('employment_type', params.employment_type)
    if (params.remote_policy) p.set('remote_policy', params.remote_policy)
    p.set('page', page)
    return `/jobs?${p.toString()}`
  }

  return (
    <div className="mx-auto max-w-7xl px-6 py-10">
      {/* Search bar */}
      <form action="/jobs" method="GET" className="relative flex items-center gap-2">
        <div className="relative flex-1">
          <svg
            className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            type="text"
            name="search"
            defaultValue={params.search ?? ''}
            placeholder="Search by job title, keyword, or skill..."
            className="w-full rounded-lg border border-border bg-background pl-11 pr-4 py-3 text-sm outline-none placeholder:text-muted-foreground focus:ring-2 focus:ring-primary focus:border-primary transition-all"
          />
        </div>
        {/* Preserve active filters in hidden fields */}
        {params.department && (
          <input type="hidden" name="department" value={params.department} />
        )}
        {params.location && (
          <input type="hidden" name="location" value={params.location} />
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
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-6 py-3 text-sm font-medium text-white transition-all hover:bg-primary/90 hover:shadow-lg"
        >
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          Search
        </button>
      </form>

      {/* Filters */}
      <div className="mt-6">
        <JobFilters categories={categories} locations={locations} />
      </div>

      {/* Active Filters */}
      {(params.department || params.employment_type || params.remote_policy || params.location) && (
        <div className="mt-4">
          <ActiveFilters />
        </div>
      )}

      {/* Results count */}
      <div className="mt-6 flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          <span className="font-semibold text-foreground">{jobs.count}</span>{' '}
          {jobs.count === 1 ? 'position' : 'positions'} found
        </p>
        {jobs.count > 0 && (
          <p className="text-xs text-muted-foreground">
            Page {params.page || '1'}
          </p>
        )}
      </div>

      {/* Job cards */}
      {jobs.results.length > 0 ? (
        <div className="mt-4 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {jobs.results.map((job) => (
            <Link
              key={job.id}
              href={`/jobs/${job.slug}`}
              className="group relative rounded-xl border border-border bg-card p-6 shadow-sm transition-all hover:shadow-lg hover:border-primary/50"
            >
              {/* Department badge */}
              <div className="absolute right-4 top-4">
                <span className="rounded-md bg-primary/10 px-2 py-1 text-xs font-medium text-primary">
                  {job.level}
                </span>
              </div>

              <h2 className="pr-16 text-lg font-semibold leading-tight group-hover:text-primary transition-colors">
                {job.title}
              </h2>
              <p className="mt-2 text-sm font-medium text-muted-foreground">
                {job.department}
              </p>

              {/* Job details */}
              <div className="mt-4 flex flex-wrap gap-2">
                <span className="inline-flex items-center gap-1 rounded-md bg-muted px-2.5 py-1 text-xs">
                  <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  {job.location_city
                    ? `${job.location_city}, ${job.location_country}`
                    : job.location_name}
                </span>
                <span className="inline-flex items-center gap-1 rounded-md bg-muted px-2.5 py-1 text-xs">
                  <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  {job.employment_type.replace('_', '-')}
                </span>
                <span className="inline-flex items-center gap-1 rounded-md bg-muted px-2.5 py-1 text-xs">
                  <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                  </svg>
                  {formatRemotePolicy(job.remote_policy)}
                </span>
              </div>

              {/* Salary */}
              {(job.salary_min || job.salary_max) && (
                <div className="mt-4 pt-4 border-t border-border">
                  <p className="text-sm font-semibold text-primary">
                    {formatSalary(job)}
                  </p>
                </div>
              )}

              {/* View details indicator */}
              <div className="mt-4 flex items-center text-sm font-medium text-primary opacity-0 group-hover:opacity-100 transition-opacity">
                View details
                <svg className="ml-1 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
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
          className="mt-10 flex items-center justify-center gap-2"
        >
          {prevPage ? (
            <Link
              href={buildPageUrl(prevPage)}
              className="inline-flex items-center gap-2 rounded-lg border border-border bg-background px-4 py-2.5 text-sm font-medium transition-all hover:bg-muted hover:border-primary/50"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Previous
            </Link>
          ) : (
            <span className="inline-flex items-center gap-2 rounded-lg border border-border bg-muted px-4 py-2.5 text-sm font-medium text-muted-foreground cursor-not-allowed">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Previous
            </span>
          )}

          {/* Page indicator */}
          <div className="px-3 py-2 text-sm">
            <span className="font-medium text-foreground">
              Page {params.page || '1'}
            </span>
            {jobs.count > 0 && (
              <span className="text-muted-foreground">
                {' '}of {Math.ceil(jobs.count / 20)}
              </span>
            )}
          </div>

          {nextPage ? (
            <Link
              href={buildPageUrl(nextPage)}
              className="inline-flex items-center gap-2 rounded-lg border border-border bg-background px-4 py-2.5 text-sm font-medium transition-all hover:bg-muted hover:border-primary/50"
            >
              Next
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          ) : (
            <span className="inline-flex items-center gap-2 rounded-lg border border-border bg-muted px-4 py-2.5 text-sm font-medium text-muted-foreground cursor-not-allowed">
              Next
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
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
            <div className="animate-pulse space-y-6">
              {/* Search skeleton */}
              <div className="h-11 rounded-lg bg-muted" />

              {/* Filters skeleton */}
              <div className="flex gap-3">
                <div className="h-10 w-48 rounded-lg bg-muted" />
                <div className="h-10 w-48 rounded-lg bg-muted" />
                <div className="h-10 w-48 rounded-lg bg-muted" />
                <div className="h-10 w-48 rounded-lg bg-muted" />
              </div>

              {/* Results count skeleton */}
              <div className="h-6 w-32 rounded bg-muted" />

              {/* Job cards skeleton */}
              <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
                {Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} className="rounded-xl border border-border bg-card p-6 space-y-4">
                    <div className="space-y-2">
                      <div className="h-6 w-3/4 rounded bg-muted" />
                      <div className="h-4 w-1/2 rounded bg-muted" />
                    </div>
                    <div className="flex gap-2">
                      <div className="h-6 w-20 rounded-md bg-muted" />
                      <div className="h-6 w-20 rounded-md bg-muted" />
                      <div className="h-6 w-20 rounded-md bg-muted" />
                    </div>
                    <div className="h-5 w-32 rounded bg-muted" />
                  </div>
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

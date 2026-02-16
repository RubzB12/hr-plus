import { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { getSavedSearch, getSavedSearchMatches } from '@/lib/dal'
import type { SavedSearch, PublicJob } from '@/types/api'

interface SavedSearchDetailPageProps {
  params: Promise<{ id: string }>
}

export async function generateMetadata({
  params,
}: SavedSearchDetailPageProps): Promise<Metadata> {
  const { id } = await params

  try {
    const search: SavedSearch = await getSavedSearch(id)
    return {
      title: `${search.name} - Saved Search`,
      description: `View jobs matching your saved search: ${search.name}`,
    }
  } catch {
    return { title: 'Saved Search Not Found' }
  }
}

export default async function SavedSearchDetailPage({
  params,
}: SavedSearchDetailPageProps) {
  const { id } = await params

  let savedSearch: SavedSearch
  let matches: { count: number; results: PublicJob[] } = { count: 0, results: [] }

  try {
    savedSearch = await getSavedSearch(id)
    matches = await getSavedSearchMatches(id)
  } catch {
    notFound()
  }

  const formatSalary = (job: PublicJob): string => {
    if (!job.salary_min && !job.salary_max) return ''
    const currency = job.salary_currency ?? 'ZAR'
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

  const formatRemotePolicy = (policy: string): string => {
    const labels: Record<string, string> = {
      onsite: 'On-site',
      remote: 'Remote',
      hybrid: 'Hybrid',
    }
    return labels[policy] ?? policy
  }

  const formatSearchParams = () => {
    const params = savedSearch.search_params
    const parts: string[] = []

    if (params.keywords || params.search) {
      parts.push(`Keywords: "${params.keywords || params.search}"`)
    }
    if (params.department) parts.push(`Department: ${params.department}`)
    if (params.location_city) parts.push(`Location: ${params.location_city}`)
    if (params.remote_policy) {
      parts.push(
        `Work Mode: ${
          params.remote_policy === 'remote'
            ? 'Remote'
            : params.remote_policy === 'hybrid'
            ? 'Hybrid'
            : 'On-site'
        }`
      )
    }
    if (params.employment_type) {
      parts.push(`Type: ${params.employment_type.replace('_', ' ')}`)
    }

    return parts
  }

  const getFrequencyLabel = (frequency: string) => {
    const labels: Record<string, string> = {
      instant: 'Instant',
      daily: 'Daily',
      weekly: 'Weekly',
      never: 'Never',
    }
    return labels[frequency] || frequency
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <Link
          href="/dashboard/saved-searches"
          className="inline-flex items-center gap-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground mb-4"
        >
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 19l-7-7 7-7"
            />
          </svg>
          Back to Saved Searches
        </Link>

        <h1 className="text-2xl font-bold">{savedSearch.name}</h1>

        {/* Status Badge */}
        <div className="mt-2 flex items-center gap-3">
          <span
            className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium ${
              savedSearch.is_active
                ? 'bg-green-100 text-green-700'
                : 'bg-gray-100 text-gray-700'
            }`}
          >
            {savedSearch.is_active ? (
              <>
                <span className="h-2 w-2 rounded-full bg-green-500"></span>
                Active
              </>
            ) : (
              <>
                <span className="h-2 w-2 rounded-full bg-gray-400"></span>
                Paused
              </>
            )}
          </span>

          <span className="text-sm text-muted-foreground">
            {getFrequencyLabel(savedSearch.alert_frequency)} alerts
          </span>
        </div>
      </div>

      {/* Search Criteria */}
      <div className="rounded-lg border border-border bg-card p-6">
        <h3 className="font-semibold mb-3">Search Criteria</h3>
        {formatSearchParams().length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {formatSearchParams().map((param, index) => (
              <span
                key={index}
                className="inline-flex items-center gap-1 rounded-md bg-muted px-3 py-1 text-sm"
              >
                {param}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">No filters applied (all jobs)</p>
        )}
      </div>

      {/* Results Count */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          <span className="font-semibold text-foreground">{matches.count}</span>{' '}
          {matches.count === 1 ? 'job' : 'jobs'} match{matches.count === 1 ? 'es' : ''} your
          search
        </p>
      </div>

      {/* Job Cards */}
      {matches.results.length > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {matches.results.map((job) => (
            <Link
              key={job.id}
              href={`/jobs/${job.slug}`}
              className="group relative rounded-xl border border-border bg-card p-6 shadow-sm transition-all hover:shadow-lg hover:border-primary/50"
            >
              {/* Level Badge */}
              <div className="absolute right-4 top-4">
                <span className="rounded-md bg-primary/10 px-2 py-1 text-xs font-medium text-primary">
                  {job.level}
                </span>
              </div>

              <h2 className="pr-16 text-lg font-semibold leading-tight group-hover:text-primary transition-colors">
                {job.title}
              </h2>
              <p className="mt-2 text-sm font-medium text-muted-foreground">{job.department}</p>

              {/* Job Details */}
              <div className="mt-4 flex flex-wrap gap-2">
                <span className="inline-flex items-center gap-1 rounded-md bg-muted px-2.5 py-1 text-xs">
                  <svg
                    className="h-3 w-3"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                  </svg>
                  {job.location_city
                    ? `${job.location_city}, ${job.location_country}`
                    : job.location_name}
                </span>
                <span className="inline-flex items-center gap-1 rounded-md bg-muted px-2.5 py-1 text-xs">
                  <svg
                    className="h-3 w-3"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                    />
                  </svg>
                  {job.employment_type.replace('_', '-')}
                </span>
                <span className="inline-flex items-center gap-1 rounded-md bg-muted px-2.5 py-1 text-xs">
                  <svg
                    className="h-3 w-3"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
                    />
                  </svg>
                  {formatRemotePolicy(job.remote_policy)}
                </span>
              </div>

              {/* Salary */}
              {(job.salary_min || job.salary_max) && (
                <div className="mt-4 pt-4 border-t border-border">
                  <p className="text-sm font-semibold text-primary">{formatSalary(job)}</p>
                </div>
              )}
            </Link>
          ))}
        </div>
      ) : (
        /* Empty State */
        <div className="rounded-lg border border-dashed border-border bg-muted/30 px-6 py-12 text-center">
          <div className="mx-auto w-12 h-12 rounded-full bg-muted flex items-center justify-center mb-4">
            <svg
              className="h-6 w-6 text-muted-foreground"
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
          </div>
          <h3 className="text-lg font-semibold">No matching jobs right now</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            We'll send you an email alert when new positions match your search criteria.
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <Link
              href="/jobs"
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary/90"
            >
              Browse All Jobs
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}

import Link from 'next/link'
import { getJobs, getCategories } from '@/lib/dal'
import type { PaginatedResponse, PublicJob, JobCategory } from '@/types/api'

function formatSalary(job: PublicJob): string {
  if (!job.salary_min && !job.salary_max) return ''
  const currency = job.salary_currency ?? 'USD'
  const fmt = (v: string) =>
    new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
      maximumFractionDigits: 0,
    }).format(Number(v))

  if (job.salary_min && job.salary_max) return `${fmt(job.salary_min)} - ${fmt(job.salary_max)}`
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

export default async function HomePage() {
  let jobs: PaginatedResponse<PublicJob> = { count: 0, next: null, previous: null, results: [] }
  let categories: JobCategory[] = []

  try {
    jobs = await getJobs()
  } catch {
    // Graceful degradation -- render page with empty jobs
  }

  try {
    categories = await getCategories()
  } catch {
    // Graceful degradation -- render page without categories
  }

  const featuredJobs = jobs.results.slice(0, 6)

  return (
    <>
      {/* Hero */}
      <section className="bg-muted py-20 sm:py-28">
        <div className="mx-auto max-w-7xl px-6 text-center">
          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
            Find Your Next Career
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-lg text-muted-foreground">
            Explore open positions across our teams and discover where you can
            make an impact.
          </p>

          <form
            action="/jobs"
            method="GET"
            className="mx-auto mt-8 flex max-w-lg items-center gap-2"
          >
            <input
              type="text"
              name="search"
              placeholder="Search jobs by title, skill, or keyword..."
              className="flex-1 rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none placeholder:text-muted-foreground focus:ring-2 focus:ring-primary"
            />
            <button
              type="submit"
              className="rounded-lg bg-primary px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-primary-dark"
            >
              Search
            </button>
          </form>
        </div>
      </section>

      {/* Featured Jobs */}
      {featuredJobs.length > 0 && (
        <section className="mx-auto max-w-7xl px-6 py-16">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold">Featured Jobs</h2>
            <Link
              href="/jobs"
              className="text-sm font-medium text-primary hover:text-primary-dark"
            >
              View all positions &rarr;
            </Link>
          </div>

          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {featuredJobs.map((job) => (
              <Link
                key={job.id}
                href={`/jobs/${job.slug}`}
                className="group rounded-lg border border-border bg-background p-6 transition-shadow hover:shadow-md"
              >
                <h3 className="font-semibold group-hover:text-primary">
                  {job.title}
                </h3>
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
        </section>
      )}

      {/* Explore by Department */}
      {categories.length > 0 && (
        <section className="bg-muted py-16">
          <div className="mx-auto max-w-7xl px-6">
            <h2 className="text-2xl font-bold">Explore by Department</h2>
            <p className="mt-2 text-muted-foreground">
              Find roles that match your expertise and interests.
            </p>

            <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {categories.map((cat) => (
                <Link
                  key={cat.department__id}
                  href={`/jobs?department=${encodeURIComponent(cat.department__name)}`}
                  className="group rounded-lg border border-border bg-background p-5 transition-shadow hover:shadow-md"
                >
                  <p className="font-semibold group-hover:text-primary">
                    {cat.department__name}
                  </p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {cat.job_count} open{' '}
                    {cat.job_count === 1 ? 'position' : 'positions'}
                  </p>
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}
    </>
  )
}

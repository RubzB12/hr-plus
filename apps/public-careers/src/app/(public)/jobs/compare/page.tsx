import type { Metadata } from 'next'
import Link from 'next/link'
import { redirect } from 'next/navigation'
import { getJobBySlug } from '@/lib/dal'
import type { PublicJobDetail } from '@/types/api'

export const metadata: Metadata = {
  title: 'Compare Jobs',
}

interface ComparePageProps {
  searchParams: Promise<{ jobs?: string }>
}

function formatSalary(job: PublicJobDetail): string {
  if (!job.salary_min && !job.salary_max) return '—'
  const currency = job.salary_currency ?? 'ZAR'
  const fmt = (v: string) =>
    new Intl.NumberFormat('en-ZA', {
      style: 'currency',
      currency,
      maximumFractionDigits: 0,
    }).format(Number(v))

  if (job.salary_min && job.salary_max)
    return `${fmt(job.salary_min)} – ${fmt(job.salary_max)}`
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

function RowLabel({ label }: { label: string }) {
  return (
    <th
      scope="row"
      className="w-36 py-3 pr-4 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground"
    >
      {label}
    </th>
  )
}

function Cell({ children }: { children: React.ReactNode }) {
  return (
    <td className="py-3 px-4 text-sm text-foreground align-top">
      {children ?? <span className="text-muted-foreground">—</span>}
    </td>
  )
}

export default async function ComparePage({ searchParams }: ComparePageProps) {
  const { jobs: jobsParam } = await searchParams

  if (!jobsParam) redirect('/jobs')

  const slugs = jobsParam
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
    .slice(0, 3) // Max 3

  if (slugs.length < 2) redirect('/jobs')

  const results = await Promise.allSettled(slugs.map((slug) => getJobBySlug(slug)))

  const jobs: PublicJobDetail[] = results
    .filter((r): r is PromiseFulfilledResult<PublicJobDetail> => r.status === 'fulfilled')
    .map((r) => r.value)

  if (jobs.length < 2) redirect('/jobs')

  return (
    <div className="mx-auto max-w-7xl px-6 py-10">
      <div className="flex items-center justify-between gap-4">
        <div>
          <Link
            href="/jobs"
            className="inline-flex items-center gap-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to jobs
          </Link>
          <h1 className="mt-4 text-3xl font-bold tracking-tight">Compare Positions</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Side-by-side comparison of {jobs.length} roles
          </p>
        </div>
      </div>

      <div className="mt-8 overflow-x-auto rounded-xl border border-border shadow-sm">
        <table className="w-full min-w-[600px] bg-card">
          <thead>
            <tr className="border-b border-border bg-muted/50">
              <th className="w-36 py-4 pr-4 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground" />
              {jobs.map((job) => (
                <th key={job.id} className="py-4 px-4 text-left">
                  <Link
                    href={`/jobs/${job.slug}`}
                    className="block font-semibold text-foreground hover:text-primary transition-colors"
                  >
                    {job.title}
                  </Link>
                  <p className="mt-0.5 text-xs text-muted-foreground">{job.department}</p>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            <tr>
              <RowLabel label="Location" />
              {jobs.map((job) => (
                <Cell key={job.id}>
                  {job.location_city
                    ? `${job.location_city}, ${job.location_country}`
                    : job.location_name}
                </Cell>
              ))}
            </tr>
            <tr className="bg-muted/20">
              <RowLabel label="Work Mode" />
              {jobs.map((job) => (
                <Cell key={job.id}>{formatRemotePolicy(job.remote_policy)}</Cell>
              ))}
            </tr>
            <tr>
              <RowLabel label="Employment" />
              {jobs.map((job) => (
                <Cell key={job.id}>
                  {job.employment_type.replace(/_/g, ' ')}
                </Cell>
              ))}
            </tr>
            <tr className="bg-muted/20">
              <RowLabel label="Level" />
              {jobs.map((job) => (
                <Cell key={job.id}>{job.level ?? '—'}</Cell>
              ))}
            </tr>
            <tr>
              <RowLabel label="Salary" />
              {jobs.map((job) => (
                <Cell key={job.id}>{formatSalary(job)}</Cell>
              ))}
            </tr>
            {jobs.some((j) => j.requirements_required.length > 0) && (
              <tr className="bg-muted/20">
                <RowLabel label="Requirements" />
                {jobs.map((job) => (
                  <Cell key={job.id}>
                    {job.requirements_required.length > 0 ? (
                      <ul className="space-y-1 text-sm">
                        {job.requirements_required.slice(0, 5).map((req, i) => (
                          <li key={i} className="flex items-start gap-1.5">
                            <svg
                              className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M5 13l4 4L19 7"
                              />
                            </svg>
                            {req}
                          </li>
                        ))}
                        {job.requirements_required.length > 5 && (
                          <li className="text-xs text-muted-foreground">
                            +{job.requirements_required.length - 5} more
                          </li>
                        )}
                      </ul>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </Cell>
                ))}
              </tr>
            )}
            <tr>
              <RowLabel label="Apply" />
              {jobs.map((job) => (
                <Cell key={job.id}>
                  <Link
                    href={`/apply/${job.slug}`}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary/90"
                  >
                    Apply Now
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </Link>
                </Cell>
              ))}
            </tr>
          </tbody>
        </table>
      </div>

      <div className="mt-6 text-center">
        <Link
          href="/jobs"
          className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
        >
          View all open positions →
        </Link>
      </div>
    </div>
  )
}

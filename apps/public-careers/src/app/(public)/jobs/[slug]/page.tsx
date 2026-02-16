import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { getJobBySlug, getSimilarJobs } from '@/lib/dal'
import type { PublicJobDetail, PublicJob } from '@/types/api'
import { ShareButtons } from '@/components/features/job-detail/share-buttons'

interface JobDetailPageProps {
  params: Promise<{ slug: string }>
}

function formatSalary(job: PublicJobDetail): string {
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

export async function generateMetadata({
  params,
}: JobDetailPageProps): Promise<Metadata> {
  const { slug } = await params

  try {
    const job: PublicJobDetail = await getJobBySlug(slug)
    const salary = formatSalary(job)
    const description = `${job.title} at HR-Plus - ${job.department}, ${job.location_city ?? job.location_name}. ${salary ? salary + '. ' : ''}Apply now.`

    return {
      title: job.title,
      description,
      openGraph: {
        title: `${job.title} | HR-Plus Careers`,
        description,
        type: 'website',
      },
    }
  } catch {
    return { title: 'Job Not Found' }
  }
}

function JobPostingJsonLd({ job }: { job: PublicJobDetail }) {
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'JobPosting',
    title: job.title,
    description: job.description,
    datePosted: job.published_at,
    employmentType: job.employment_type?.toUpperCase().replace(' ', '_'),
    jobLocationType: job.remote_policy === 'remote' ? 'TELECOMMUTE' : undefined,
    hiringOrganization: {
      '@type': 'Organization',
      name: 'HR-Plus',
      sameAs: process.env.NEXT_PUBLIC_SITE_URL ?? 'https://careers.hrplus.com',
    },
    jobLocation: {
      '@type': 'Place',
      address: {
        '@type': 'PostalAddress',
        addressLocality: job.location_city ?? undefined,
        addressCountry: job.location_country ?? undefined,
      },
    },
    baseSalary:
      job.salary_min || job.salary_max
        ? {
            '@type': 'MonetaryAmount',
            currency: job.salary_currency ?? 'USD',
            value: {
              '@type': 'QuantitativeValue',
              minValue: job.salary_min ? Number(job.salary_min) : undefined,
              maxValue: job.salary_max ? Number(job.salary_max) : undefined,
              unitText: 'YEAR',
            },
          }
        : undefined,
  }

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
    />
  )
}

export default async function JobDetailPage({ params }: JobDetailPageProps) {
  const { slug } = await params

  let job: PublicJobDetail
  try {
    job = await getJobBySlug(slug)
  } catch {
    notFound()
  }

  let similarJobs: PublicJob[] = []
  try {
    const response = await getSimilarJobs(job.id)
    similarJobs = Array.isArray(response) ? response : response.results ?? []
  } catch {
    // Graceful degradation
  }

  const salary = formatSalary(job)

  return (
    <>
      <JobPostingJsonLd job={job} />

      <section className="border-b border-border bg-gradient-to-b from-muted to-background py-12">
        <div className="mx-auto max-w-7xl px-6">
          <Link
            href="/jobs"
            className="inline-flex items-center gap-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to all positions
          </Link>

          <div className="mt-6 flex items-start justify-between gap-6">
            <div className="flex-1">
              <h1 className="text-4xl font-bold tracking-tight">{job.title}</h1>
              <p className="mt-3 text-lg text-muted-foreground">{job.department}</p>

              <div className="mt-6 flex flex-wrap gap-2 text-sm">
                <span className="inline-flex items-center gap-1.5 rounded-lg bg-background px-3 py-1.5 border border-border shadow-sm">
                  <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  {job.location_city
                    ? `${job.location_city}, ${job.location_country}`
                    : job.location_name}
                </span>
                <span className="inline-flex items-center gap-1.5 rounded-lg bg-background px-3 py-1.5 border border-border shadow-sm">
                  <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  {job.employment_type.replace('_', ' ')}
                </span>
                <span className="inline-flex items-center gap-1.5 rounded-lg bg-background px-3 py-1.5 border border-border shadow-sm">
                  <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                  </svg>
                  {formatRemotePolicy(job.remote_policy)}
                </span>
                {job.level && (
                  <span className="inline-flex items-center gap-1.5 rounded-lg bg-background px-3 py-1.5 border border-border shadow-sm">
                    <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                    </svg>
                    {job.level}
                  </span>
                )}
                {salary && (
                  <span className="inline-flex items-center gap-1.5 rounded-lg bg-primary/10 px-3 py-1.5 font-semibold text-primary border border-primary/20">
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {salary}
                  </span>
                )}
              </div>

              {/* Mobile Action Buttons */}
              <div className="mt-6 flex items-center gap-3 lg:hidden">
                <ShareButtons
                  job={{
                    title: job.title,
                    slug: job.slug,
                    department: job.department,
                    location_city: job.location_city,
                    location_name: job.location_name,
                  }}
                />
                <Link
                  href={`/apply/${job.id}`}
                  className="flex-1 inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-6 py-3 text-sm font-medium text-white shadow-lg transition-all hover:bg-primary/90 hover:shadow-xl"
                >
                  Apply Now
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </Link>
              </div>
            </div>

            {/* Desktop Action Buttons */}
            <div className="hidden lg:flex items-center gap-3">
              <ShareButtons
                job={{
                  title: job.title,
                  slug: job.slug,
                  department: job.department,
                  location_city: job.location_city,
                  location_name: job.location_name,
                }}
              />
              <Link
                href={`/apply/${job.id}`}
                className="inline-flex items-center gap-2 rounded-lg bg-primary px-6 py-3 text-sm font-medium text-white shadow-lg transition-all hover:bg-primary/90 hover:shadow-xl"
              >
                Apply Now
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
            </div>
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-7xl px-6 py-10 lg:flex lg:gap-12">
        {/* Main content */}
        <article className="flex-1">
          {/* Description */}
          <section>
            <h2 className="text-xl font-semibold">About This Role</h2>
            <div
              className="prose prose-neutral mt-4 max-w-none text-foreground"
              dangerouslySetInnerHTML={{ __html: job.description }}
            />
          </section>

          {/* Required qualifications */}
          {job.requirements_required.length > 0 && (
            <section className="mt-10">
              <h2 className="text-xl font-semibold">Requirements</h2>
              <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-muted-foreground">
                {job.requirements_required.map((req, i) => (
                  <li key={i}>{req}</li>
                ))}
              </ul>
            </section>
          )}

          {/* Preferred qualifications */}
          {job.requirements_preferred.length > 0 && (
            <section className="mt-10">
              <h2 className="text-xl font-semibold">Nice to Have</h2>
              <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-muted-foreground">
                {job.requirements_preferred.map((req, i) => (
                  <li key={i}>{req}</li>
                ))}
              </ul>
            </section>
          )}

          {/* Apply CTA */}
          <div className="mt-12 rounded-xl border border-primary/20 bg-gradient-to-br from-primary/5 to-primary/10 p-8 text-center">
            <div className="mx-auto max-w-md">
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                <svg className="h-6 w-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h2 className="text-xl font-bold">Ready to Apply?</h2>
              <p className="mt-2 text-sm text-muted-foreground">
                Submit your application and our team will review it shortly. We typically respond within 3-5 business days.
              </p>
              <Link
                href={`/apply/${job.id}`}
                className="mt-6 inline-flex items-center gap-2 rounded-lg bg-primary px-8 py-3 text-sm font-medium text-white shadow-lg transition-all hover:bg-primary/90 hover:shadow-xl"
              >
                Apply for this Position
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
            </div>
          </div>
        </article>

        {/* Sidebar: Similar jobs */}
        {similarJobs.length > 0 && (
          <aside className="mt-12 lg:mt-0 lg:w-80 lg:shrink-0">
            <div className="sticky top-6">
              <div className="flex items-center gap-2">
                <svg className="h-5 w-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <h2 className="text-lg font-semibold">Similar Positions</h2>
              </div>
              <p className="mt-1 text-sm text-muted-foreground">
                You might also be interested in these roles
              </p>
              <div className="mt-4 space-y-3">
                {similarJobs.slice(0, 5).map((sj) => (
                  <Link
                    key={sj.id}
                    href={`/jobs/${sj.slug}`}
                    className="block rounded-xl border border-border bg-card p-4 shadow-sm transition-all hover:shadow-md hover:border-primary/50"
                  >
                    <p className="font-semibold text-sm leading-snug">{sj.title}</p>
                    <p className="mt-2 flex items-center gap-1 text-xs text-muted-foreground">
                      <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                      </svg>
                      {sj.department}
                    </p>
                    <p className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
                      <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      {sj.location_city ?? sj.location_name}
                    </p>
                  </Link>
                ))}
              </div>
              <Link
                href="/jobs"
                className="mt-4 block text-center text-sm font-medium text-primary hover:text-primary/80 transition-colors"
              >
                View all open positions →
              </Link>
            </div>
          </aside>
        )}
      </div>
    </>
  )
}

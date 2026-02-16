'use client'

import { useRouter, useSearchParams } from 'next/navigation'
import { useCallback, useEffect, useState } from 'react'
import type { JobFacets } from '@/types/api'
import { getJobFacets } from '@/lib/dal'

const EMPLOYMENT_TYPE_LABELS: Record<string, string> = {
  full_time: 'Full-time',
  part_time: 'Part-time',
  contract: 'Contract',
  internship: 'Internship',
}

const REMOTE_POLICY_LABELS: Record<string, string> = {
  onsite: 'On-site',
  remote: 'Remote',
  hybrid: 'Hybrid',
}

export default function JobFiltersEnhanced() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [facets, setFacets] = useState<JobFacets | null>(null)
  const [loading, setLoading] = useState(true)

  const currentSearch = searchParams.get('search') ?? ''
  const currentDepartment = searchParams.get('department') ?? ''
  const currentLocation = searchParams.get('location') ?? ''
  const currentType = searchParams.get('employment_type') ?? ''
  const currentRemote = searchParams.get('remote_policy') ?? ''
  const currentLevel = searchParams.get('level') ?? ''

  // Fetch facets whenever filters change
  useEffect(() => {
    const fetchFacets = async () => {
      try {
        setLoading(true)
        const data = await getJobFacets({
          search: currentSearch || undefined,
          department: currentDepartment || undefined,
          location: currentLocation || undefined,
          employment_type: currentType || undefined,
          remote_policy: currentRemote || undefined,
          level: currentLevel || undefined,
        })
        setFacets(data)
      } catch (error) {
        console.error('Failed to fetch facets:', error)
        // Graceful degradation - component still works without counts
      } finally {
        setLoading(false)
      }
    }

    fetchFacets()
  }, [currentSearch, currentDepartment, currentLocation, currentType, currentRemote, currentLevel])

  const updateFilter = useCallback(
    (key: string, value: string) => {
      const params = new URLSearchParams(searchParams.toString())

      if (value) {
        params.set(key, value)
      } else {
        params.delete(key)
      }

      // Reset to first page when filters change
      params.delete('page')

      router.push(`/jobs?${params.toString()}`)
    },
    [router, searchParams]
  )

  const getCount = (value: string, facetArray: Array<{ value?: string; name?: string; count: number }>) => {
    const item = facetArray.find(f => f.value === value || f.name === value)
    return item?.count ?? 0
  }

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
      {/* Department Filter */}
      <select
        value={currentDepartment}
        onChange={(e) => updateFilter('department', e.target.value)}
        aria-label="Filter by department"
        className="rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
        disabled={loading}
      >
        <option value="">All Departments</option>
        {facets?.departments.map((dept) => (
          <option key={dept.id} value={dept.name}>
            {dept.name} ({dept.count})
          </option>
        ))}
      </select>

      {/* Location Filter */}
      <select
        value={currentLocation}
        onChange={(e) => updateFilter('location', e.target.value)}
        aria-label="Filter by location"
        className="rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
        disabled={loading}
      >
        <option value="">All Locations</option>
        {facets?.locations.map((loc) => (
          <option key={loc.id} value={loc.name}>
            {loc.name} ({loc.count})
          </option>
        ))}
      </select>

      {/* Employment Type Filter */}
      <select
        value={currentType}
        onChange={(e) => updateFilter('employment_type', e.target.value)}
        aria-label="Filter by employment type"
        className="rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
        disabled={loading}
      >
        <option value="">All Types</option>
        {Object.entries(EMPLOYMENT_TYPE_LABELS).map(([value, label]) => {
          const count = facets ? getCount(value, facets.employment_types) : '...'
          return (
            <option key={value} value={value}>
              {label} ({count})
            </option>
          )
        })}
      </select>

      {/* Remote Policy Filter */}
      <select
        value={currentRemote}
        onChange={(e) => updateFilter('remote_policy', e.target.value)}
        aria-label="Filter by remote policy"
        className="rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
        disabled={loading}
      >
        <option value="">All Work Modes</option>
        {Object.entries(REMOTE_POLICY_LABELS).map(([value, label]) => {
          const count = facets ? getCount(value, facets.remote_policies) : '...'
          return (
            <option key={value} value={value}>
              {label} ({count})
            </option>
          )
        })}
      </select>

      {/* Level Filter - NEW! */}
      <select
        value={currentLevel}
        onChange={(e) => updateFilter('level', e.target.value)}
        aria-label="Filter by level"
        className="rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
        disabled={loading}
      >
        <option value="">All Levels</option>
        {facets?.levels.map((level) => (
          <option key={level.id} value={level.name}>
            {level.name} ({level.count})
          </option>
        ))}
      </select>

      {/* Loading indicator */}
      {loading && (
        <div className="text-xs text-muted-foreground flex items-center gap-2">
          <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          Updating...
        </div>
      )}
    </div>
  )
}

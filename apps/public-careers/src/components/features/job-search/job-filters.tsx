'use client'

import { useRouter, useSearchParams } from 'next/navigation'
import { useCallback } from 'react'
import type { JobCategory } from '@/types/api'

const EMPLOYMENT_TYPES = [
  { value: 'full_time', label: 'Full-time' },
  { value: 'part_time', label: 'Part-time' },
  { value: 'contract', label: 'Contract' },
  { value: 'internship', label: 'Internship' },
]

const REMOTE_POLICIES = [
  { value: 'onsite', label: 'On-site' },
  { value: 'remote', label: 'Remote' },
  { value: 'hybrid', label: 'Hybrid' },
]

interface JobFiltersProps {
  categories: JobCategory[]
  locations: Array<{ id: string; name: string }>
}

export default function JobFilters({ categories, locations }: JobFiltersProps) {
  const router = useRouter()
  const searchParams = useSearchParams()

  const currentDepartment = searchParams.get('department') ?? ''
  const currentLocation = searchParams.get('location') ?? ''
  const currentType = searchParams.get('employment_type') ?? ''
  const currentRemote = searchParams.get('remote_policy') ?? ''

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

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
      <select
        value={currentDepartment}
        onChange={(e) => updateFilter('department', e.target.value)}
        aria-label="Filter by department"
        className="rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
      >
        <option value="">All Departments</option>
        {categories.map((cat) => (
          <option key={cat.department__id} value={cat.department__name}>
            {cat.department__name} ({cat.job_count})
          </option>
        ))}
      </select>

      <select
        value={currentLocation}
        onChange={(e) => updateFilter('location', e.target.value)}
        aria-label="Filter by location"
        className="rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
      >
        <option value="">All Locations</option>
        {locations.map((loc) => (
          <option key={loc.id} value={loc.name}>
            {loc.name}
          </option>
        ))}
      </select>

      <select
        value={currentType}
        onChange={(e) => updateFilter('employment_type', e.target.value)}
        aria-label="Filter by employment type"
        className="rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
      >
        <option value="">All Types</option>
        {EMPLOYMENT_TYPES.map((t) => (
          <option key={t.value} value={t.value}>
            {t.label}
          </option>
        ))}
      </select>

      <select
        value={currentRemote}
        onChange={(e) => updateFilter('remote_policy', e.target.value)}
        aria-label="Filter by remote policy"
        className="rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
      >
        <option value="">All Work Modes</option>
        {REMOTE_POLICIES.map((r) => (
          <option key={r.value} value={r.value}>
            {r.label}
          </option>
        ))}
      </select>
    </div>
  )
}

'use client'

import { useRouter, useSearchParams } from 'next/navigation'
import { useCallback } from 'react'

export default function ActiveFilters() {
  const router = useRouter()
  const searchParams = useSearchParams()

  const removeFilter = useCallback(
    (key: string) => {
      const params = new URLSearchParams(searchParams.toString())
      params.delete(key)
      params.delete('page') // Reset to first page
      router.push(`/jobs?${params.toString()}`)
    },
    [router, searchParams]
  )

  const clearAll = useCallback(() => {
    const params = new URLSearchParams()
    const search = searchParams.get('search')
    if (search) params.set('search', search) // Preserve search query
    router.push(`/jobs?${params.toString()}`)
  }, [router, searchParams])

  const activeFilters = []

  const department = searchParams.get('department')
  if (department) {
    activeFilters.push({ key: 'department', label: 'Department', value: department })
  }

  const location = searchParams.get('location')
  if (location) {
    activeFilters.push({ key: 'location', label: 'Location', value: location })
  }

  const employmentType = searchParams.get('employment_type')
  if (employmentType) {
    const label = employmentType.replace('_', '-')
    activeFilters.push({ key: 'employment_type', label: 'Type', value: label })
  }

  const remotePolicy = searchParams.get('remote_policy')
  if (remotePolicy) {
    const labels: Record<string, string> = {
      onsite: 'On-site',
      remote: 'Remote',
      hybrid: 'Hybrid',
    }
    activeFilters.push({
      key: 'remote_policy',
      label: 'Work Mode',
      value: labels[remotePolicy] ?? remotePolicy,
    })
  }

  if (activeFilters.length === 0) return null

  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-sm font-medium text-muted-foreground">Active filters:</span>
      {activeFilters.map((filter) => (
        <button
          key={filter.key}
          onClick={() => removeFilter(filter.key)}
          className="inline-flex items-center gap-1.5 rounded-full bg-primary/10 px-3 py-1 text-sm font-medium text-primary transition-colors hover:bg-primary/20"
        >
          <span className="text-xs text-primary/70">{filter.label}:</span>
          {filter.value}
          <svg
            className="h-3.5 w-3.5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      ))}
      {activeFilters.length > 1 && (
        <button
          onClick={clearAll}
          className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors underline underline-offset-4"
        >
          Clear all
        </button>
      )}
    </div>
  )
}

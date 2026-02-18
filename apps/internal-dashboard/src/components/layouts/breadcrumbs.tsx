'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { ChevronRight, Home } from 'lucide-react'

const SEGMENT_LABELS: Record<string, string> = {
  dashboard: 'Dashboard',
  requisitions: 'Requisitions',
  applications: 'Applications',
  candidates: 'Candidates',
  interviews: 'Interviews',
  offers: 'Offers',
  analytics: 'Analytics',
  pipeline: 'Pipeline',
  settings: 'Settings',
  compare: 'Compare',
  departments: 'Departments',
  locations: 'Locations',
  users: 'Users',
  new: 'New Requisition',
  create: 'Create Offer',
  schedule: 'Schedule Interview',
}

function isId(segment: string) {
  // UUID or numeric ID
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(segment) ||
    /^\d+$/.test(segment)
}

function segmentLabel(segment: string): string {
  if (SEGMENT_LABELS[segment]) return SEGMENT_LABELS[segment]
  if (isId(segment)) return 'Detail'
  return segment.charAt(0).toUpperCase() + segment.slice(1).replace(/-/g, ' ')
}

export function Breadcrumbs() {
  const pathname = usePathname()
  const segments = pathname.split('/').filter(Boolean)

  // Only render for nested paths (skip top-level pages like /dashboard)
  if (segments.length <= 1) return null

  const crumbs = segments.map((seg, i) => ({
    href: '/' + segments.slice(0, i + 1).join('/'),
    label: segmentLabel(seg),
    isLast: i === segments.length - 1,
  }))

  return (
    <nav aria-label="Breadcrumb" className="flex items-center gap-1 text-sm text-muted-foreground">
      <Link href="/dashboard" className="hover:text-foreground transition-colors shrink-0">
        <Home className="h-3.5 w-3.5" />
        <span className="sr-only">Dashboard</span>
      </Link>
      {crumbs.map(({ href, label, isLast }) => (
        <span key={href} className="flex items-center gap-1">
          <ChevronRight className="h-3.5 w-3.5 shrink-0" />
          {isLast ? (
            <span className="text-foreground font-medium truncate max-w-[160px]">{label}</span>
          ) : (
            <Link
              href={href}
              className="hover:text-foreground transition-colors truncate max-w-[120px]"
            >
              {label}
            </Link>
          )}
        </span>
      ))}
    </nav>
  )
}

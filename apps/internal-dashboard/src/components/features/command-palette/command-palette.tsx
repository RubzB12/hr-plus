'use client'

import { useEffect, useRef, useState, useTransition } from 'react'
import { useRouter } from 'next/navigation'
import {
  LayoutDashboard,
  FileText,
  Users,
  UserSearch,
  Calendar,
  DollarSign,
  BarChart3,
  Settings,
  Briefcase,
  Search,
  ArrowRight,
  Loader2,
} from 'lucide-react'
import { globalSearch } from '@/app/(dashboard)/search-action'

interface NavItem {
  title: string
  href: string
  icon: React.ElementType
  description: string
}

const NAV_ITEMS: NavItem[] = [
  { title: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, description: 'Overview & metrics' },
  { title: 'Requisitions', href: '/requisitions', icon: FileText, description: 'Job openings' },
  { title: 'Applications', href: '/applications', icon: Briefcase, description: 'All applications' },
  { title: 'Candidates', href: '/candidates', icon: UserSearch, description: 'Candidate search' },
  { title: 'Interviews', href: '/interviews', icon: Calendar, description: 'Scheduled interviews' },
  { title: 'Offers', href: '/offers', icon: DollarSign, description: 'Offer management' },
  { title: 'Analytics', href: '/analytics', icon: BarChart3, description: 'Reports & insights' },
  { title: 'Settings', href: '/settings', icon: Settings, description: 'App configuration' },
  { title: 'Users', href: '/settings/users', icon: Users, description: 'Manage team members' },
]

interface SearchResults {
  applications: Array<{ id: string; candidate_name: string; requisition_title: string; status: string }>
  candidates: Array<{ id: string; candidate_name: string; candidate_email: string }>
}

export function CommandPalette() {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResults>({ applications: [], candidates: [] })
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [isPending, startTransition] = useTransition()
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const router = useRouter()

  // Listen for Cmd+K / Ctrl+K and custom open event from SearchTrigger
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setOpen((prev) => !prev)
      }
      if (e.key === 'Escape') {
        setOpen(false)
      }
    }
    function handleOpenEvent() {
      setOpen((prev) => !prev)
    }
    window.addEventListener('keydown', handleKeyDown)
    window.addEventListener('open-command-palette', handleOpenEvent)
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      window.removeEventListener('open-command-palette', handleOpenEvent)
    }
  }, [])

  // Focus input when opened
  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 50)
      setQuery('')
      setResults({ applications: [], candidates: [] })
      setSelectedIndex(0)
    }
  }, [open])

  // Debounced search
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (query.trim().length < 2) {
      setResults({ applications: [], candidates: [] })
      return
    }
    debounceRef.current = setTimeout(() => {
      startTransition(async () => {
        const data = await globalSearch(query)
        setResults(data)
        setSelectedIndex(0)
      })
    }, 300)
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [query])

  // Build the flat list of all navigable items for keyboard nav
  const filteredNav = query.trim().length === 0
    ? NAV_ITEMS
    : NAV_ITEMS.filter(
        (item) =>
          item.title.toLowerCase().includes(query.toLowerCase()) ||
          item.description.toLowerCase().includes(query.toLowerCase())
      )

  type ResultItem =
    | { type: 'nav'; item: NavItem }
    | { type: 'application'; item: SearchResults['applications'][number] }
    | { type: 'candidate'; item: SearchResults['candidates'][number] }

  const allItems: ResultItem[] = [
    ...filteredNav.map((item) => ({ type: 'nav' as const, item })),
    ...results.applications.map((item) => ({ type: 'application' as const, item })),
    ...results.candidates.map((item) => ({ type: 'candidate' as const, item })),
  ]

  function getItemHref(entry: ResultItem): string {
    if (entry.type === 'nav') return entry.item.href
    if (entry.type === 'application') return `/applications/${entry.item.id}`
    return `/candidates/${entry.item.id}`
  }

  function navigate(href: string) {
    setOpen(false)
    router.push(href)
  }

  // Arrow key navigation
  function handleKeyDownInPalette(e: React.KeyboardEvent) {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedIndex((i) => Math.min(i + 1, allItems.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedIndex((i) => Math.max(i - 1, 0))
    } else if (e.key === 'Enter') {
      e.preventDefault()
      const selected = allItems[selectedIndex]
      if (selected) navigate(getItemHref(selected))
    }
  }

  const hasResults = results.applications.length > 0 || results.candidates.length > 0
  const noResults = query.trim().length >= 2 && !isPending && !hasResults && filteredNav.length === 0

  if (!open) return null

  let globalIdx = 0

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]"
      onClick={() => setOpen(false)}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />

      {/* Palette */}
      <div
        className="relative w-full max-w-xl mx-4 rounded-xl border bg-background shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={handleKeyDownInPalette}
      >
        {/* Search Input */}
        <div className="flex items-center border-b px-4 py-3 gap-3">
          <Search className="h-4 w-4 text-muted-foreground shrink-0" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Search pages, applications, candidates..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
          />
          {isPending && <Loader2 className="h-4 w-4 text-muted-foreground animate-spin shrink-0" />}
          <kbd className="hidden sm:inline-flex items-center gap-1 rounded border px-2 py-0.5 text-[10px] font-mono text-muted-foreground bg-muted">
            ESC
          </kbd>
        </div>

        {/* Results */}
        <div className="max-h-[60vh] overflow-y-auto">
          {noResults ? (
            <p className="py-8 text-center text-sm text-muted-foreground">
              No results for &ldquo;{query}&rdquo;
            </p>
          ) : (
            <div className="py-2">
              {/* Navigation section */}
              {filteredNav.length > 0 && (
                <div>
                  <p className="px-4 py-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                    {query.trim().length === 0 ? 'Navigation' : 'Pages'}
                  </p>
                  {filteredNav.map((item) => {
                    const idx = globalIdx++
                    const isSelected = selectedIndex === idx
                    const Icon = item.icon
                    return (
                      <button
                        key={item.href}
                        onClick={() => navigate(item.href)}
                        onMouseEnter={() => setSelectedIndex(idx)}
                        className={`w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors ${
                          isSelected ? 'bg-muted' : 'hover:bg-muted/50'
                        }`}
                      >
                        <div className="flex h-7 w-7 items-center justify-center rounded-md border bg-background shrink-0">
                          <Icon className="h-3.5 w-3.5 text-muted-foreground" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium">{item.title}</p>
                          <p className="text-xs text-muted-foreground">{item.description}</p>
                        </div>
                        <ArrowRight className={`h-3.5 w-3.5 shrink-0 transition-opacity ${isSelected ? 'opacity-100 text-primary' : 'opacity-0'}`} />
                      </button>
                    )
                  })}
                </div>
              )}

              {/* Applications section */}
              {results.applications.length > 0 && (
                <div>
                  <p className="px-4 py-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wide mt-1">
                    Applications
                  </p>
                  {results.applications.map((app) => {
                    const idx = globalIdx++
                    const isSelected = selectedIndex === idx
                    return (
                      <button
                        key={app.id}
                        onClick={() => navigate(`/applications/${app.id}`)}
                        onMouseEnter={() => setSelectedIndex(idx)}
                        className={`w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors ${
                          isSelected ? 'bg-muted' : 'hover:bg-muted/50'
                        }`}
                      >
                        <div className="flex h-7 w-7 items-center justify-center rounded-md border bg-background shrink-0">
                          <Briefcase className="h-3.5 w-3.5 text-muted-foreground" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{app.candidate_name}</p>
                          <p className="text-xs text-muted-foreground truncate">{app.requisition_title}</p>
                        </div>
                        <span className="text-xs text-muted-foreground capitalize shrink-0">{app.status}</span>
                        <ArrowRight className={`h-3.5 w-3.5 shrink-0 transition-opacity ${isSelected ? 'opacity-100 text-primary' : 'opacity-0'}`} />
                      </button>
                    )
                  })}
                </div>
              )}

              {/* Candidates section */}
              {results.candidates.length > 0 && (
                <div>
                  <p className="px-4 py-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wide mt-1">
                    Candidates
                  </p>
                  {results.candidates.map((candidate) => {
                    const idx = globalIdx++
                    const isSelected = selectedIndex === idx
                    return (
                      <button
                        key={candidate.id}
                        onClick={() => navigate(`/candidates/${candidate.id}`)}
                        onMouseEnter={() => setSelectedIndex(idx)}
                        className={`w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors ${
                          isSelected ? 'bg-muted' : 'hover:bg-muted/50'
                        }`}
                      >
                        <div className="flex h-7 w-7 items-center justify-center rounded-md border bg-background shrink-0">
                          <UserSearch className="h-3.5 w-3.5 text-muted-foreground" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{candidate.candidate_name}</p>
                          <p className="text-xs text-muted-foreground truncate">{candidate.candidate_email}</p>
                        </div>
                        <ArrowRight className={`h-3.5 w-3.5 shrink-0 transition-opacity ${isSelected ? 'opacity-100 text-primary' : 'opacity-0'}`} />
                      </button>
                    )
                  })}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer hint */}
        <div className="flex items-center gap-4 border-t px-4 py-2.5 text-[11px] text-muted-foreground">
          <span className="flex items-center gap-1">
            <kbd className="rounded border px-1 py-0.5 font-mono bg-muted">↑↓</kbd>
            Navigate
          </span>
          <span className="flex items-center gap-1">
            <kbd className="rounded border px-1 py-0.5 font-mono bg-muted">↵</kbd>
            Open
          </span>
          <span className="flex items-center gap-1">
            <kbd className="rounded border px-1 py-0.5 font-mono bg-muted">ESC</kbd>
            Close
          </span>
        </div>
      </div>
    </div>
  )
}

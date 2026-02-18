'use client'

import { Search } from 'lucide-react'

export function SearchTrigger() {
  function openPalette() {
    window.dispatchEvent(new CustomEvent('open-command-palette'))
  }

  return (
    <button
      onClick={openPalette}
      className="hidden sm:flex items-center gap-2 rounded-md border bg-muted/50 px-3 py-1.5 text-sm text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
    >
      <Search className="h-3.5 w-3.5" />
      <span>Search...</span>
      <kbd className="ml-2 inline-flex items-center gap-0.5 rounded border bg-background px-1.5 py-0.5 text-[10px] font-mono">
        <span>⌘</span>K
      </kbd>
    </button>
  )
}

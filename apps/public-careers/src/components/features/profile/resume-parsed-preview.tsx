'use client'

import { useState, useTransition } from 'react'
import { importResumeSectionsAction } from '@/app/dashboard/profile/actions'

interface ParsedExperience {
  title?: string
  company?: string
  start_date?: string
  end_date?: string | null
  is_current?: boolean
}

interface ParsedEducation {
  institution?: string
  degree?: string
  field_of_study?: string
}

interface Props {
  parsedData: Record<string, any>
}

export function ResumeParsedPreview({ parsedData }: Props) {
  const [selectedSections, setSelectedSections] = useState<Set<string>>(
    new Set(['skills', 'experiences', 'education'])
  )
  const [isPending, startTransition] = useTransition()
  const [result, setResult] = useState<{ success: boolean; message?: string } | null>(null)

  const skills: string[] = parsedData?.skills ?? []
  const experiences: ParsedExperience[] = parsedData?.experiences ?? []
  const education: ParsedEducation[] = parsedData?.education ?? []

  const hasContent = skills.length > 0 || experiences.length > 0 || education.length > 0
  if (!hasContent) return null

  const toggleSection = (section: string) => {
    setSelectedSections(prev => {
      const next = new Set(prev)
      if (next.has(section)) next.delete(section)
      else next.add(section)
      return next
    })
  }

  const handleImport = () => {
    const sections = Array.from(selectedSections)
    if (sections.length === 0) return

    startTransition(async () => {
      const res = await importResumeSectionsAction(sections)
      setResult(res)
    })
  }

  if (result?.success) {
    return (
      <div className="rounded-xl border border-green-200 bg-green-50 p-4">
        <div className="flex items-center gap-2 text-sm text-green-700">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5 shrink-0">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clipRule="evenodd" />
          </svg>
          <span className="font-medium">{result.message}</span>
        </div>
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-blue-200 bg-blue-50/50 p-5">
      <div className="flex items-start gap-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-100">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="h-4 w-4 text-blue-600">
            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
          </svg>
        </div>
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-blue-900">Import from your resume</h3>
          <p className="mt-0.5 text-xs text-blue-700">
            We found data in your resume. Select sections to import into your profile.
          </p>
        </div>
      </div>

      <div className="mt-4 space-y-3">
        {skills.length > 0 && (
          <label className="flex cursor-pointer items-start gap-3">
            <input
              type="checkbox"
              checked={selectedSections.has('skills')}
              onChange={() => toggleSection('skills')}
              className="mt-0.5 rounded border-gray-300 text-blue-600"
            />
            <div>
              <span className="text-sm font-medium text-gray-900">
                Skills <span className="font-normal text-gray-500">({skills.length} found)</span>
              </span>
              <p className="mt-0.5 text-xs text-gray-500 line-clamp-1">
                {skills.slice(0, 6).join(', ')}{skills.length > 6 ? `, +${skills.length - 6} more` : ''}
              </p>
            </div>
          </label>
        )}

        {experiences.length > 0 && (
          <label className="flex cursor-pointer items-start gap-3">
            <input
              type="checkbox"
              checked={selectedSections.has('experiences')}
              onChange={() => toggleSection('experiences')}
              className="mt-0.5 rounded border-gray-300 text-blue-600"
            />
            <div>
              <span className="text-sm font-medium text-gray-900">
                Work Experience <span className="font-normal text-gray-500">({experiences.length} found)</span>
              </span>
              <p className="mt-0.5 text-xs text-gray-500 line-clamp-1">
                {experiences.slice(0, 2).map(e => e.title && e.company ? `${e.title} at ${e.company}` : e.title ?? e.company ?? '').filter(Boolean).join(', ')}
              </p>
            </div>
          </label>
        )}

        {education.length > 0 && (
          <label className="flex cursor-pointer items-start gap-3">
            <input
              type="checkbox"
              checked={selectedSections.has('education')}
              onChange={() => toggleSection('education')}
              className="mt-0.5 rounded border-gray-300 text-blue-600"
            />
            <div>
              <span className="text-sm font-medium text-gray-900">
                Education <span className="font-normal text-gray-500">({education.length} found)</span>
              </span>
              <p className="mt-0.5 text-xs text-gray-500 line-clamp-1">
                {education.slice(0, 2).map(e => e.degree && e.institution ? `${e.degree} — ${e.institution}` : e.institution ?? e.degree ?? '').filter(Boolean).join(', ')}
              </p>
            </div>
          </label>
        )}
      </div>

      {result?.message && !result.success && (
        <div className="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
          {result.message}
        </div>
      )}

      <button
        onClick={handleImport}
        disabled={isPending || selectedSections.size === 0}
        className="mt-4 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
      >
        {isPending ? 'Importing…' : `Import Selected (${selectedSections.size})`}
      </button>
    </div>
  )
}

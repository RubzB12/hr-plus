'use client'

import { useState } from 'react'
import { createExperience, updateExperience, deleteExperience } from '@/app/dashboard/profile/profile-actions'

interface WorkExperience {
  id?: string
  company_name: string
  title: string
  start_date: string
  end_date: string | null
  is_current: boolean
  description: string
}

interface WorkExperienceSectionProps {
  experiences: WorkExperience[]
}

export function WorkExperienceSection({ experiences: initialExperiences }: WorkExperienceSectionProps) {
  const [experiences, setExperiences] = useState<WorkExperience[]>(initialExperiences)
  const [isAdding, setIsAdding] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [formData, setFormData] = useState<WorkExperience>({
    company_name: '',
    title: '',
    start_date: '',
    end_date: null,
    is_current: false,
    description: '',
  })
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const resetForm = () => {
    setFormData({
      company_name: '',
      title: '',
      start_date: '',
      end_date: null,
      is_current: false,
      description: '',
    })
    setIsAdding(false)
    setEditingId(null)
    setError(null)
  }

  const handleAdd = () => {
    setIsAdding(true)
    setEditingId(null)
    resetForm()
  }

  const handleEdit = (exp: WorkExperience) => {
    setFormData(exp)
    setEditingId(exp.id!)
    setIsAdding(false)
  }

  const handleSave = async () => {
    setError(null)
    setIsSaving(true)

    try {
      let savedExp: WorkExperience
      if (editingId) {
        savedExp = await updateExperience(editingId, formData) as WorkExperience
        setExperiences(experiences.map(exp => exp.id === editingId ? savedExp : exp))
      } else {
        savedExp = await createExperience(formData) as WorkExperience
        setExperiences([savedExp, ...experiences])
      }

      resetForm()
    } catch (err: any) {
      setError(err.message || 'Failed to save work experience')
    } finally {
      setIsSaving(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this work experience?')) {
      return
    }

    try {
      await deleteExperience(id)
      setExperiences(experiences.filter(exp => exp.id !== id))
    } catch (err) {
      alert('Failed to delete work experience')
    }
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Work Experience</h3>
        {!isAdding && !editingId && (
          <button
            onClick={handleAdd}
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Experience
          </button>
        )}
      </div>

      {/* Form */}
      {(isAdding || editingId) && (
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
          <h4 className="mb-4 font-semibold">
            {editingId ? 'Edit Experience' : 'Add New Experience'}
          </h4>

          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label htmlFor="company_name" className="block text-sm font-medium mb-1.5">
                  Company *
                </label>
                <input
                  id="company_name"
                  type="text"
                  required
                  value={formData.company_name}
                  onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                  className="block w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm outline-none transition-colors focus:border-primary focus:ring-2 focus:ring-primary/20"
                />
              </div>
              <div>
                <label htmlFor="title" className="block text-sm font-medium mb-1.5">
                  Job Title *
                </label>
                <input
                  id="title"
                  type="text"
                  required
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="block w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm outline-none transition-colors focus:border-primary focus:ring-2 focus:ring-primary/20"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label htmlFor="start_date" className="block text-sm font-medium mb-1.5">
                  Start Date *
                </label>
                <input
                  id="start_date"
                  type="date"
                  required
                  value={formData.start_date}
                  onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                  className="block w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm outline-none transition-colors focus:border-primary focus:ring-2 focus:ring-primary/20"
                />
              </div>
              <div>
                <label htmlFor="end_date" className="block text-sm font-medium mb-1.5">
                  End Date
                </label>
                <input
                  id="end_date"
                  type="date"
                  disabled={formData.is_current}
                  value={formData.end_date || ''}
                  onChange={(e) => setFormData({ ...formData, end_date: e.target.value || null })}
                  className="block w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm outline-none transition-colors focus:border-primary focus:ring-2 focus:ring-primary/20 disabled:bg-muted disabled:cursor-not-allowed"
                />
              </div>
            </div>

            <div className="flex items-center gap-2">
              <input
                id="is_current"
                type="checkbox"
                checked={formData.is_current}
                onChange={(e) => setFormData({ ...formData, is_current: e.target.checked, end_date: e.target.checked ? null : formData.end_date })}
                className="h-4 w-4 rounded border-border text-primary focus:ring-2 focus:ring-primary/20"
              />
              <label htmlFor="is_current" className="text-sm font-medium">
                I currently work here
              </label>
            </div>

            <div>
              <label htmlFor="description" className="block text-sm font-medium mb-1.5">
                Description
              </label>
              <textarea
                id="description"
                rows={4}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Describe your responsibilities and achievements..."
                className="block w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm outline-none transition-colors focus:border-primary focus:ring-2 focus:ring-primary/20"
              />
            </div>

            {error && (
              <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                {error}
              </div>
            )}

            <div className="flex items-center gap-3">
              <button
                onClick={handleSave}
                disabled={isSaving || !formData.company_name || !formData.title || !formData.start_date}
                className="inline-flex items-center gap-2 rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-white shadow-sm transition-all hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSaving ? 'Saving...' : 'Save'}
              </button>
              <button
                onClick={resetForm}
                disabled={isSaving}
                className="inline-flex items-center gap-2 rounded-lg border border-border bg-background px-6 py-2.5 text-sm font-medium transition-all hover:bg-muted disabled:opacity-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* List */}
      {experiences.length === 0 && !isAdding ? (
        <div className="rounded-xl border-2 border-dashed border-border bg-muted/30 p-8 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-muted">
            <svg className="h-6 w-6 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <p className="mt-3 text-sm text-muted-foreground">
            No work experience added yet
          </p>
          <button
            onClick={handleAdd}
            className="mt-4 inline-flex items-center gap-2 text-sm font-medium text-primary hover:text-primary/80"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add your first experience
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {experiences.map((exp) => (
            <div
              key={exp.id}
              className="rounded-xl border border-border bg-card p-5 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h4 className="font-semibold">{exp.title}</h4>
                  <p className="text-sm text-muted-foreground">{exp.company_name}</p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {formatDate(exp.start_date)} -{' '}
                    {exp.is_current ? 'Present' : exp.end_date ? formatDate(exp.end_date) : 'N/A'}
                  </p>
                  {exp.description && (
                    <p className="mt-2 text-sm text-muted-foreground whitespace-pre-wrap">
                      {exp.description}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleEdit(exp)}
                    className="rounded-lg p-2 text-muted-foreground hover:bg-muted hover:text-foreground"
                  >
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button
                    onClick={() => handleDelete(exp.id!)}
                    className="rounded-lg p-2 text-red-600 hover:bg-red-50"
                  >
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

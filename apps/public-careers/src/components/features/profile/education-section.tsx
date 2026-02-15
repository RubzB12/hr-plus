'use client'

import { useState } from 'react'
import { createEducation, updateEducation, deleteEducation } from '@/app/dashboard/profile/profile-actions'

interface Education {
  id?: string
  institution: string
  degree: string
  field_of_study: string
  start_date: string
  end_date: string | null
  gpa: string | null
}

interface EducationSectionProps {
  education: Education[]
}

export function EducationSection({ education: initialEducation }: EducationSectionProps) {
  const [education, setEducation] = useState<Education[]>(initialEducation)
  const [isAdding, setIsAdding] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [formData, setFormData] = useState<Education>({
    institution: '',
    degree: '',
    field_of_study: '',
    start_date: '',
    end_date: null,
    gpa: null,
  })
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const resetForm = () => {
    setFormData({
      institution: '',
      degree: '',
      field_of_study: '',
      start_date: '',
      end_date: null,
      gpa: null,
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

  const handleEdit = (edu: Education) => {
    setFormData(edu)
    setEditingId(edu.id!)
    setIsAdding(false)
  }

  const handleSave = async () => {
    setError(null)
    setIsSaving(true)

    try {
      let savedEdu: Education
      if (editingId) {
        savedEdu = await updateEducation(editingId, formData) as Education
        setEducation(education.map(edu => edu.id === editingId ? savedEdu : edu))
      } else {
        savedEdu = await createEducation(formData) as Education
        setEducation([savedEdu, ...education])
      }

      resetForm()
    } catch (err: any) {
      setError(err.message || 'Failed to save education')
    } finally {
      setIsSaving(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this education record?')) {
      return
    }

    try {
      await deleteEducation(id)
      setEducation(education.filter(edu => edu.id !== id))
    } catch (err) {
      alert('Failed to delete education record')
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
        <h3 className="text-lg font-semibold">Education</h3>
        {!isAdding && !editingId && (
          <button
            onClick={handleAdd}
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Education
          </button>
        )}
      </div>

      {/* Form */}
      {(isAdding || editingId) && (
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
          <h4 className="mb-4 font-semibold">
            {editingId ? 'Edit Education' : 'Add New Education'}
          </h4>

          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label htmlFor="institution" className="block text-sm font-medium mb-1.5">
                  Institution *
                </label>
                <input
                  id="institution"
                  type="text"
                  required
                  value={formData.institution}
                  onChange={(e) => setFormData({ ...formData, institution: e.target.value })}
                  placeholder="University of California"
                  className="block w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm outline-none transition-colors focus:border-primary focus:ring-2 focus:ring-primary/20"
                />
              </div>
              <div>
                <label htmlFor="degree" className="block text-sm font-medium mb-1.5">
                  Degree *
                </label>
                <input
                  id="degree"
                  type="text"
                  required
                  value={formData.degree}
                  onChange={(e) => setFormData({ ...formData, degree: e.target.value })}
                  placeholder="Bachelor of Science"
                  className="block w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm outline-none transition-colors focus:border-primary focus:ring-2 focus:ring-primary/20"
                />
              </div>
            </div>

            <div>
              <label htmlFor="field_of_study" className="block text-sm font-medium mb-1.5">
                Field of Study
              </label>
              <input
                id="field_of_study"
                type="text"
                value={formData.field_of_study}
                onChange={(e) => setFormData({ ...formData, field_of_study: e.target.value })}
                placeholder="Computer Science"
                className="block w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm outline-none transition-colors focus:border-primary focus:ring-2 focus:ring-primary/20"
              />
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
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
                  value={formData.end_date || ''}
                  onChange={(e) => setFormData({ ...formData, end_date: e.target.value || null })}
                  className="block w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm outline-none transition-colors focus:border-primary focus:ring-2 focus:ring-primary/20"
                />
              </div>
              <div>
                <label htmlFor="gpa" className="block text-sm font-medium mb-1.5">
                  GPA
                </label>
                <input
                  id="gpa"
                  type="text"
                  value={formData.gpa || ''}
                  onChange={(e) => setFormData({ ...formData, gpa: e.target.value || null })}
                  placeholder="3.85"
                  className="block w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm outline-none transition-colors focus:border-primary focus:ring-2 focus:ring-primary/20"
                />
              </div>
            </div>

            {error && (
              <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                {error}
              </div>
            )}

            <div className="flex items-center gap-3">
              <button
                onClick={handleSave}
                disabled={isSaving || !formData.institution || !formData.degree || !formData.start_date}
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
      {education.length === 0 && !isAdding ? (
        <div className="rounded-xl border-2 border-dashed border-border bg-muted/30 p-8 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-muted">
            <svg className="h-6 w-6 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </div>
          <p className="mt-3 text-sm text-muted-foreground">
            No education records added yet
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {education.map((edu) => (
            <div
              key={edu.id}
              className="rounded-xl border border-border bg-card p-5 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h4 className="font-semibold">{edu.degree}</h4>
                  <p className="text-sm text-muted-foreground">{edu.institution}</p>
                  {edu.field_of_study && (
                    <p className="mt-0.5 text-sm text-muted-foreground">{edu.field_of_study}</p>
                  )}
                  <p className="mt-1 text-xs text-muted-foreground">
                    {formatDate(edu.start_date)} - {edu.end_date ? formatDate(edu.end_date) : 'Present'}
                    {edu.gpa && ` • GPA: ${edu.gpa}`}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleEdit(edu)}
                    className="rounded-lg p-2 text-muted-foreground hover:bg-muted hover:text-foreground"
                  >
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button
                    onClick={() => handleDelete(edu.id!)}
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

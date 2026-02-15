'use client'

import { useState } from 'react'
import { createSkill, deleteSkill } from '@/app/dashboard/profile/profile-actions'

interface Skill {
  id?: string
  name: string
  proficiency: string
  years_experience: number | null
}

interface SkillsSectionProps {
  skills: Skill[]
}

export function SkillsSection({ skills: initialSkills }: SkillsSectionProps) {
  const [skills, setSkills] = useState<Skill[]>(initialSkills)
  const [isAdding, setIsAdding] = useState(false)
  const [skillName, setSkillName] = useState('')
  const [proficiency, setProficiency] = useState<string>('')
  const [yearsExperience, setYearsExperience] = useState<string>('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleAdd = async () => {
    if (!skillName.trim()) {
      setError('Please enter a skill name')
      return
    }

    setError(null)
    setIsSubmitting(true)

    try {
      const newSkill = await createSkill({
        name: skillName.trim(),
        proficiency: proficiency || '',
        years_experience: yearsExperience ? parseInt(yearsExperience) : null,
      }) as Skill

      setSkills([...skills, newSkill])
      setSkillName('')
      setProficiency('')
      setYearsExperience('')
      setIsAdding(false)
    } catch (err: any) {
      setError(err.message || 'Failed to add skill')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Remove "${name}" from your skills?`)) {
      return
    }

    try {
      await deleteSkill(id)
      setSkills(skills.filter(skill => skill.id !== id))
    } catch (err) {
      alert('Failed to remove skill')
    }
  }

  const proficiencyColors: Record<string, string> = {
    beginner: 'bg-blue-100 text-blue-700 border-blue-200',
    intermediate: 'bg-green-100 text-green-700 border-green-200',
    advanced: 'bg-purple-100 text-purple-700 border-purple-200',
    expert: 'bg-orange-100 text-orange-700 border-orange-200',
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Skills</h3>
        {!isAdding && (
          <button
            onClick={() => setIsAdding(true)}
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Skill
          </button>
        )}
      </div>

      {/* Add Form */}
      {isAdding && (
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
          <h4 className="mb-4 font-semibold">Add New Skill</h4>

          <div className="space-y-4">
            <div>
              <label htmlFor="skill_name" className="block text-sm font-medium mb-1.5">
                Skill Name *
              </label>
              <input
                id="skill_name"
                type="text"
                required
                value={skillName}
                onChange={(e) => setSkillName(e.target.value)}
                placeholder="e.g., Python, Project Management, Data Analysis"
                className="block w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm outline-none transition-colors focus:border-primary focus:ring-2 focus:ring-primary/20"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && skillName.trim()) {
                    e.preventDefault()
                    handleAdd()
                  }
                }}
              />
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label htmlFor="proficiency" className="block text-sm font-medium mb-1.5">
                  Proficiency Level
                </label>
                <select
                  id="proficiency"
                  value={proficiency}
                  onChange={(e) => setProficiency(e.target.value)}
                  className="block w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm outline-none transition-colors focus:border-primary focus:ring-2 focus:ring-primary/20"
                >
                  <option value="">Select level (optional)</option>
                  <option value="beginner">Beginner</option>
                  <option value="intermediate">Intermediate</option>
                  <option value="advanced">Advanced</option>
                  <option value="expert">Expert</option>
                </select>
              </div>
              <div>
                <label htmlFor="years_experience" className="block text-sm font-medium mb-1.5">
                  Years of Experience
                </label>
                <input
                  id="years_experience"
                  type="number"
                  min="0"
                  max="50"
                  value={yearsExperience}
                  onChange={(e) => setYearsExperience(e.target.value)}
                  placeholder="0"
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
                onClick={handleAdd}
                disabled={isSubmitting || !skillName.trim()}
                className="inline-flex items-center gap-2 rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-white shadow-sm transition-all hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Adding...' : 'Add Skill'}
              </button>
              <button
                onClick={() => {
                  setIsAdding(false)
                  setSkillName('')
                  setProficiency('')
                  setYearsExperience('')
                  setError(null)
                }}
                disabled={isSubmitting}
                className="inline-flex items-center gap-2 rounded-lg border border-border bg-background px-6 py-2.5 text-sm font-medium transition-all hover:bg-muted disabled:opacity-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Skills List */}
      {skills.length === 0 && !isAdding ? (
        <div className="rounded-xl border-2 border-dashed border-border bg-muted/30 p-8 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-muted">
            <svg className="h-6 w-6 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <p className="mt-3 text-sm text-muted-foreground">
            No skills added yet
          </p>
        </div>
      ) : (
        <div className="flex flex-wrap gap-2">
          {skills.map((skill) => (
            <div
              key={skill.id}
              className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium transition-all hover:shadow-sm ${
                skill.proficiency && proficiencyColors[skill.proficiency]
                  ? proficiencyColors[skill.proficiency]
                  : 'border-border bg-muted/50 text-foreground hover:bg-muted'
              }`}
            >
              <span>{skill.name}</span>
              {skill.years_experience !== null && skill.years_experience > 0 && (
                <span className="text-xs opacity-75">
                  ({skill.years_experience}y)
                </span>
              )}
              <button
                onClick={() => handleDelete(skill.id!, skill.name)}
                className="ml-1 rounded-full p-0.5 hover:bg-black/10"
                aria-label={`Remove ${skill.name}`}
              >
                <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          ))}
        </div>
      )}

      {skills.length > 0 && (
        <p className="text-xs text-muted-foreground">
          <svg className="inline h-3.5 w-3.5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Color indicates proficiency level:
          <span className="ml-2 inline-flex items-center gap-1">
            <span className="inline-block h-2 w-2 rounded-full bg-blue-500"></span> Beginner
          </span>
          <span className="ml-2 inline-flex items-center gap-1">
            <span className="inline-block h-2 w-2 rounded-full bg-green-500"></span> Intermediate
          </span>
          <span className="ml-2 inline-flex items-center gap-1">
            <span className="inline-block h-2 w-2 rounded-full bg-purple-500"></span> Advanced
          </span>
          <span className="ml-2 inline-flex items-center gap-1">
            <span className="inline-block h-2 w-2 rounded-full bg-orange-500"></span> Expert
          </span>
        </p>
      )}
    </div>
  )
}

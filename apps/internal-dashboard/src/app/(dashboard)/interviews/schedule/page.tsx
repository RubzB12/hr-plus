'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, Calendar, Clock, Video, MapPin, Users, FileText } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { scheduleInterview } from './actions'

interface Application {
  id: string
  application_id: string
  candidate_name: string
  requisition_title: string
}

interface InternalUser {
  id: string
  user_name: string
  title: string
}

export default function ScheduleInterviewPage() {
  const router = useRouter()
  const [applications, setApplications] = useState<Application[]>([])
  const [interviewers, setInterviewers] = useState<InternalUser[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')

  const [formData, setFormData] = useState({
    application_id: '',
    type: 'video',
    date: '',
    start_time: '',
    end_time: '',
    timezone: 'UTC',
    location: '',
    video_link: '',
    prep_notes_interviewer: '',
    prep_notes_candidate: '',
    selected_interviewers: [] as string[],
  })

  useEffect(() => {
    // Fetch applications and interviewers
    fetchApplications()
    fetchInterviewers()
  }, [])

  const fetchApplications = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/internal/applications/?status=screening,interview`,
        { credentials: 'include' }
      )
      if (response.ok) {
        const data = await response.json()
        setApplications(data.results || [])
      }
    } catch (err) {
      console.error('Failed to fetch applications:', err)
    }
  }

  const fetchInterviewers = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/internal/users/`,
        { credentials: 'include' }
      )
      if (response.ok) {
        const data = await response.json()
        setInterviewers(data.results || [])
      }
    } catch (err) {
      console.error('Failed to fetch interviewers:', err)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      // Combine date and time into ISO datetime
      const scheduled_start = `${formData.date}T${formData.start_time}:00`
      const scheduled_end = `${formData.date}T${formData.end_time}:00`

      const submitFormData = new FormData()
      submitFormData.append('application_id', formData.application_id)
      submitFormData.append('type', formData.type)
      submitFormData.append('scheduled_start', scheduled_start)
      submitFormData.append('scheduled_end', scheduled_end)
      submitFormData.append('timezone', formData.timezone)
      submitFormData.append('location', formData.location)
      submitFormData.append('video_link', formData.video_link)
      submitFormData.append('prep_notes_interviewer', formData.prep_notes_interviewer)
      submitFormData.append('prep_notes_candidate', formData.prep_notes_candidate)
      submitFormData.append('interviewer_ids', JSON.stringify(formData.selected_interviewers))

      const result = await scheduleInterview(submitFormData)

      if (result.success) {
        router.push('/interviews')
      } else {
        setError(result.error || 'Failed to schedule interview')
      }
    } catch (err: any) {
      setError(err.message || 'Failed to schedule interview')
    } finally {
      setLoading(false)
    }
  }

  const toggleInterviewer = (id: string) => {
    setFormData(prev => ({
      ...prev,
      selected_interviewers: prev.selected_interviewers.includes(id)
        ? prev.selected_interviewers.filter(i => i !== id)
        : [...prev.selected_interviewers, id]
    }))
  }

  const filteredApplications = applications.filter(app =>
    app.candidate_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    app.requisition_title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    app.application_id.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const selectedApplication = applications.find(a => a.id === formData.application_id)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" asChild>
          <Link href="/interviews" className="flex items-center gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back to Interviews
          </Link>
        </Button>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Schedule Interview</h1>
          <p className="text-muted-foreground mt-2">
            Create a new interview for a candidate
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Application Selection */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Select Application
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Search Applications</label>
              <Input
                type="text"
                placeholder="Search by candidate name, position, or application ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            <div className="space-y-2 max-h-64 overflow-y-auto">
              {filteredApplications.map((app) => (
                <button
                  key={app.id}
                  type="button"
                  onClick={() => setFormData({ ...formData, application_id: app.id })}
                  className={`w-full text-left rounded-lg border p-3 transition-colors ${
                    formData.application_id === app.id
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:bg-muted/50'
                  }`}
                >
                  <p className="font-medium">{app.candidate_name}</p>
                  <p className="text-sm text-muted-foreground">{app.requisition_title}</p>
                  <p className="text-xs text-muted-foreground mt-1">ID: {app.application_id}</p>
                </button>
              ))}
              {filteredApplications.length === 0 && (
                <p className="text-sm text-muted-foreground text-center py-8">
                  No applications found
                </p>
              )}
            </div>

            {selectedApplication && (
              <div className="rounded-lg bg-muted p-3">
                <p className="text-sm font-medium">Selected:</p>
                <p className="text-sm">{selectedApplication.candidate_name} - {selectedApplication.requisition_title}</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Interview Details */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Interview Details
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium">Interview Type *</label>
                <select
                  required
                  value={formData.type}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                >
                  <option value="phone_screen">Phone Screen</option>
                  <option value="video">Video Interview</option>
                  <option value="onsite">On-site Interview</option>
                  <option value="panel">Panel Interview</option>
                  <option value="technical">Technical Interview</option>
                  <option value="behavioral">Behavioral Interview</option>
                  <option value="case_study">Case Study</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Date *</label>
                <Input
                  type="date"
                  required
                  value={formData.date}
                  onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                  min={new Date().toISOString().split('T')[0]}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Start Time *</label>
                <Input
                  type="time"
                  required
                  value={formData.start_time}
                  onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">End Time *</label>
                <Input
                  type="time"
                  required
                  value={formData.end_time}
                  onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                />
              </div>
            </div>

            {(formData.type === 'video' || formData.type === 'phone_screen') && (
              <div className="space-y-2">
                <label className="text-sm font-medium flex items-center gap-2">
                  <Video className="h-4 w-4" />
                  Video Conference Link
                </label>
                <Input
                  type="url"
                  placeholder="https://meet.google.com/..."
                  value={formData.video_link}
                  onChange={(e) => setFormData({ ...formData, video_link: e.target.value })}
                />
              </div>
            )}

            {formData.type === 'onsite' && (
              <div className="space-y-2">
                <label className="text-sm font-medium flex items-center gap-2">
                  <MapPin className="h-4 w-4" />
                  Location
                </label>
                <Input
                  type="text"
                  placeholder="Building A, Conference Room 201"
                  value={formData.location}
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                />
              </div>
            )}
          </CardContent>
        </Card>

        {/* Interviewers */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Select Interviewers
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-2 md:grid-cols-2">
              {interviewers.map((interviewer) => (
                <button
                  key={interviewer.id}
                  type="button"
                  onClick={() => toggleInterviewer(interviewer.id)}
                  className={`text-left rounded-lg border p-3 transition-colors ${
                    formData.selected_interviewers.includes(interviewer.id)
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:bg-muted/50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">{interviewer.user_name}</p>
                      <p className="text-sm text-muted-foreground">{interviewer.title}</p>
                    </div>
                    {formData.selected_interviewers.includes(interviewer.id) && (
                      <span className="text-primary">✓</span>
                    )}
                  </div>
                </button>
              ))}
            </div>
            <p className="text-sm text-muted-foreground mt-4">
              {formData.selected_interviewers.length} interviewer{formData.selected_interviewers.length !== 1 ? 's' : ''} selected
            </p>
          </CardContent>
        </Card>

        {/* Notes */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Preparation Notes
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Notes for Interviewer</label>
              <textarea
                rows={4}
                placeholder="Background info, focus areas, questions to ask..."
                value={formData.prep_notes_interviewer}
                onChange={(e) => setFormData({ ...formData, prep_notes_interviewer: e.target.value })}
                className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Notes for Candidate</label>
              <textarea
                rows={4}
                placeholder="What to prepare, topics to review, what to bring..."
                value={formData.prep_notes_candidate}
                onChange={(e) => setFormData({ ...formData, prep_notes_candidate: e.target.value })}
                className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              />
            </div>
          </CardContent>
        </Card>

        {/* Error Display */}
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-4">
          <Button
            type="submit"
            disabled={loading || !formData.application_id || !formData.date || !formData.start_time || !formData.end_time}
            className="flex-1 md:flex-initial"
          >
            {loading ? 'Scheduling...' : 'Schedule Interview'}
          </Button>
          <Button type="button" variant="outline" asChild>
            <Link href="/interviews">Cancel</Link>
          </Button>
        </div>
      </form>
    </div>
  )
}

import Link from 'next/link'
import { getInterviews } from '@/lib/dal'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Calendar, Video, MapPin, Users, Clock, Plus } from 'lucide-react'

export const metadata = {
  title: 'Interviews — HR-Plus',
}

interface InterviewParticipant {
  id: string
  interviewer_name: string
  role: string
  rsvp_status: string
}

interface Interview {
  id: string
  application_id: string
  candidate_name: string
  requisition_title: string
  type: string
  status: string
  scheduled_start: string
  scheduled_end: string
  location: string
  video_link: string
  participants: InterviewParticipant[]
}

const statusVariant: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  scheduled: 'outline',
  confirmed: 'default',
  in_progress: 'secondary',
  completed: 'secondary',
  cancelled: 'destructive',
  rescheduled: 'outline',
  no_show: 'destructive',
}

const typeLabels: Record<string, string> = {
  phone_screen: 'Phone Screen',
  video: 'Video',
  onsite: 'On-site',
  panel: 'Panel',
  technical: 'Technical',
  behavioral: 'Behavioral',
  case_study: 'Case Study',
  other: 'Other',
}

function formatDateTime(dateStr: string) {
  const date = new Date(dateStr)
  return {
    date: date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    }),
    time: date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    }),
    dayOfWeek: date.toLocaleDateString('en-US', { weekday: 'short' }),
  }
}

function getDuration(start: string, end: string) {
  const startDate = new Date(start)
  const endDate = new Date(end)
  const minutes = Math.round((endDate.getTime() - startDate.getTime()) / (1000 * 60))
  if (minutes < 60) return `${minutes}m`
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`
}

function isUpcoming(dateStr: string) {
  return new Date(dateStr) > new Date()
}

export default async function InterviewsPage() {
  const data = await getInterviews()
  const interviews: Interview[] = data.results || []

  // Separate upcoming and past interviews
  const upcomingInterviews = interviews.filter(i =>
    isUpcoming(i.scheduled_start) && i.status !== 'cancelled'
  )
  const pastInterviews = interviews.filter(i =>
    !isUpcoming(i.scheduled_start) || i.status === 'cancelled' || i.status === 'completed'
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Interviews</h1>
          <p className="text-muted-foreground mt-2">
            Manage and schedule candidate interviews
          </p>
        </div>
        <Button asChild>
          <Link href="/interviews/schedule" className="flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Schedule Interview
          </Link>
        </Button>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Upcoming</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{upcomingInterviews.length}</div>
            <p className="text-xs text-muted-foreground">
              Next 30 days
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Today</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {upcomingInterviews.filter(i => {
                const today = new Date().toDateString()
                return new Date(i.scheduled_start).toDateString() === today
              }).length}
            </div>
            <p className="text-xs text-muted-foreground">
              Scheduled for today
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">This Week</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {upcomingInterviews.filter(i => {
                const weekFromNow = new Date()
                weekFromNow.setDate(weekFromNow.getDate() + 7)
                const interviewDate = new Date(i.scheduled_start)
                return interviewDate <= weekFromNow && interviewDate >= new Date()
              }).length}
            </div>
            <p className="text-xs text-muted-foreground">
              Next 7 days
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Upcoming Interviews */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Upcoming Interviews</h2>
        {upcomingInterviews.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <Calendar className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No upcoming interviews</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Schedule an interview to get started
              </p>
              <Button asChild>
                <Link href="/interviews/schedule">
                  <Plus className="h-4 w-4 mr-2" />
                  Schedule Interview
                </Link>
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {upcomingInterviews.map((interview) => {
              const { date, time, dayOfWeek } = formatDateTime(interview.scheduled_start)
              const duration = getDuration(interview.scheduled_start, interview.scheduled_end)

              return (
                <Card key={interview.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-semibold">{interview.candidate_name}</h3>
                          <Badge variant={statusVariant[interview.status] || 'outline'} className="text-xs">
                            {interview.status}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">{interview.requisition_title}</p>
                      </div>
                      <Badge variant="secondary">
                        {typeLabels[interview.type] || interview.type}
                      </Badge>
                    </div>

                    <div className="space-y-2 mb-4">
                      <div className="flex items-center gap-2 text-sm">
                        <Calendar className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium">{dayOfWeek}, {date}</span>
                      </div>
                      <div className="flex items-center gap-2 text-sm">
                        <Clock className="h-4 w-4 text-muted-foreground" />
                        <span>{time} ({duration})</span>
                      </div>
                      {interview.video_link && (
                        <div className="flex items-center gap-2 text-sm">
                          <Video className="h-4 w-4 text-muted-foreground" />
                          <a
                            href={interview.video_link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary hover:underline"
                          >
                            Join video call
                          </a>
                        </div>
                      )}
                      {interview.location && !interview.video_link && (
                        <div className="flex items-center gap-2 text-sm">
                          <MapPin className="h-4 w-4 text-muted-foreground" />
                          <span>{interview.location}</span>
                        </div>
                      )}
                    </div>

                    {interview.participants && interview.participants.length > 0 && (
                      <div className="mb-4">
                        <p className="text-xs font-medium text-muted-foreground mb-1.5">Interviewers</p>
                        <div className="flex flex-wrap gap-1">
                          {interview.participants.map((p) => (
                            <Badge key={p.id} variant="outline" className="text-xs">
                              {p.interviewer_name}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="flex items-center gap-2">
                      <Button size="sm" variant="outline" asChild className="flex-1">
                        <Link href={`/applications/${interview.application_id}`}>
                          View Application
                        </Link>
                      </Button>
                      <Button size="sm" asChild className="flex-1">
                        <Link href={`/interviews/${interview.id}`}>
                          View Details
                        </Link>
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        )}
      </div>

      {/* Past Interviews */}
      {pastInterviews.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold mb-4">Past Interviews</h2>
          <div className="space-y-2">
            {pastInterviews.slice(0, 5).map((interview) => {
              const { date, time } = formatDateTime(interview.scheduled_start)

              return (
                <Card key={interview.id} className="hover:bg-muted/50 transition-colors">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{interview.candidate_name}</span>
                          <span className="text-sm text-muted-foreground">•</span>
                          <span className="text-sm text-muted-foreground">{interview.requisition_title}</span>
                          <Badge variant={statusVariant[interview.status] || 'outline'} className="text-xs">
                            {interview.status}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground mt-1">
                          {date} at {time} • {typeLabels[interview.type] || interview.type}
                        </p>
                      </div>
                      <Button size="sm" variant="ghost" asChild>
                        <Link href={`/interviews/${interview.id}`}>
                          View
                        </Link>
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
            {pastInterviews.length > 5 && (
              <p className="text-sm text-muted-foreground text-center py-2">
                And {pastInterviews.length - 5} more past interviews
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

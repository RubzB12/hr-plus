'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { TrendingUp, Users, Clock, Target, Award, Filter } from 'lucide-react'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']

export default function AnalyticsPage() {
  const [loading, setLoading] = useState(true)
  const [showFilters, setShowFilters] = useState(false)
  const [dateRange, setDateRange] = useState({
    start_date: '',
    end_date: '',
  })

  const [executiveData, setExecutiveData] = useState<any>(null)
  const [timeToFillData, setTimeToFillData] = useState<any>(null)
  const [sourceData, setSourceData] = useState<any>(null)
  const [interviewerData, setInterviewerData] = useState<any>(null)

  useEffect(() => {
    fetchAnalytics()
  }, [])

  const fetchAnalytics = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (dateRange.start_date) params.append('start_date', dateRange.start_date)
      if (dateRange.end_date) params.append('end_date', dateRange.end_date)

      const [exec, ttf, source, interviewer] = await Promise.all([
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/internal/analytics/dashboard/executive/?${params}`, {
          credentials: 'include',
        }).then(r => r.ok ? r.json() : null),
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/internal/analytics/time-to-fill/?${params}`, {
          credentials: 'include',
        }).then(r => r.ok ? r.json() : null),
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/internal/analytics/source-effectiveness/?${params}`, {
          credentials: 'include',
        }).then(r => r.ok ? r.json() : null),
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/internal/analytics/interviewer-calibration/?${params}`, {
          credentials: 'include',
        }).then(r => r.ok ? r.json() : null),
      ])

      setExecutiveData(exec)
      setTimeToFillData(ttf)
      setSourceData(source)
      setInterviewerData(interviewer)
    } catch (error) {
      console.error('Analytics fetch error:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleApplyFilters = () => {
    fetchAnalytics()
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold">Analytics Dashboard</h1>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map(i => (
            <Card key={i} className="animate-pulse">
              <CardContent className="p-6">
                <div className="h-20 bg-muted rounded"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  const metrics = executiveData ? [
    {
      title: 'Total Hires',
      value: executiveData.total_hires || 0,
      change: '+12%',
      icon: Users,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      title: 'Avg Time to Fill',
      value: `${executiveData.avg_time_to_fill || 0} days`,
      change: '-5%',
      icon: Clock,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      title: 'Offer Accept Rate',
      value: `${executiveData.offer_accept_rate || 0}%`,
      change: '+8%',
      icon: Target,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
    },
    {
      title: 'Quality of Hire',
      value: `${executiveData.quality_of_hire || 0}/5`,
      change: '+0.3',
      icon: Award,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
    },
  ] : []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Analytics Dashboard</h1>
          <p className="text-muted-foreground mt-2">
            Comprehensive insights into your hiring performance
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center gap-2"
        >
          <Filter className="h-4 w-4" />
          {showFilters ? 'Hide Filters' : 'Show Filters'}
        </Button>
      </div>

      {/* Date Range Filters */}
      {showFilters && (
        <Card>
          <CardHeader>
            <CardTitle>Date Range</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4 items-end">
              <div className="space-y-2 flex-1">
                <label className="text-sm font-medium">Start Date</label>
                <Input
                  type="date"
                  value={dateRange.start_date}
                  onChange={(e) => setDateRange({ ...dateRange, start_date: e.target.value })}
                />
              </div>
              <div className="space-y-2 flex-1">
                <label className="text-sm font-medium">End Date</label>
                <Input
                  type="date"
                  value={dateRange.end_date}
                  onChange={(e) => setDateRange({ ...dateRange, end_date: e.target.value })}
                />
              </div>
              <Button onClick={handleApplyFilters}>Apply</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {metrics.map((metric) => {
          const Icon = metric.icon
          return (
            <Card key={metric.title}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {metric.title}
                </CardTitle>
                <div className={`rounded-full p-2 ${metric.bgColor}`}>
                  <Icon className={`h-4 w-4 ${metric.color}`} />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metric.value}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  <span className="text-green-600">{metric.change}</span> from last period
                </p>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Charts Row 1 */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Time to Fill Trend */}
        {timeToFillData && timeToFillData.by_month && (
          <Card>
            <CardHeader>
              <CardTitle>Time to Fill Trend</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={timeToFillData.by_month}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="avg_days"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    name="Days"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}

        {/* Source Effectiveness */}
        {sourceData && sourceData.by_source && (
          <Card>
            <CardHeader>
              <CardTitle>Applications by Source</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={sourceData.by_source}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({name, percent}: any) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="count"
                  >
                    {sourceData.by_source.map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Charts Row 2 */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Pipeline Conversion */}
        {executiveData && executiveData.pipeline_metrics && (
          <Card>
            <CardHeader>
              <CardTitle>Pipeline Conversion Rates</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={executiveData.pipeline_metrics}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="stage" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="conversion_rate" fill="#10b981" name="Conversion %" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}

        {/* Interviewer Performance */}
        {interviewerData && interviewerData.by_interviewer && (
          <Card>
            <CardHeader>
              <CardTitle>Top Interviewers (by volume)</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={interviewerData.by_interviewer.slice(0, 5)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="interviews_conducted" fill="#8b5cf6" name="Interviews" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Source Effectiveness Table */}
      {sourceData && sourceData.by_source && (
        <Card>
          <CardHeader>
            <CardTitle>Source Effectiveness Details</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2">Source</th>
                    <th className="text-right p-2">Applications</th>
                    <th className="text-right p-2">Hires</th>
                    <th className="text-right p-2">Conversion Rate</th>
                    <th className="text-right p-2">Avg Time to Fill</th>
                  </tr>
                </thead>
                <tbody>
                  {sourceData.by_source.map((source: any, index: number) => (
                    <tr key={index} className="border-b">
                      <td className="p-2 font-medium">{source.name}</td>
                      <td className="text-right p-2">{source.count}</td>
                      <td className="text-right p-2">{source.hires || 0}</td>
                      <td className="text-right p-2">
                        {source.conversion_rate ? `${source.conversion_rate}%` : 'N/A'}
                      </td>
                      <td className="text-right p-2">
                        {source.avg_time_to_fill ? `${source.avg_time_to_fill} days` : 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

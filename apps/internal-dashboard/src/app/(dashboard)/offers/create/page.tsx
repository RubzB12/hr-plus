import { getApplications, getDepartments, getJobLevels, getInternalUsers } from '@/lib/dal'
import { CreateOfferForm } from '@/components/features/offers/create-offer-form'

export const metadata = {
  title: 'Create Offer — HR-Plus',
}

export default async function CreateOfferPage() {
  const [applicationsData, departmentsData, jobLevelsData, usersData] = await Promise.all([
    getApplications({ status: 'active' }),
    getDepartments(),
    getJobLevels(),
    getInternalUsers(),
  ])

  const applications = applicationsData.results || []
  const departments = departmentsData.results || []
  const jobLevels = jobLevelsData.results || []
  const users = usersData.results || []

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Create Job Offer</h1>
        <p className="text-muted-foreground mt-2">
          Extend an offer to a qualified candidate
        </p>
      </div>

      <CreateOfferForm
        applications={applications}
        departments={departments}
        jobLevels={jobLevels}
        managers={users}
      />
    </div>
  )
}

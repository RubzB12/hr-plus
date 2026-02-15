import { cookies } from 'next/headers'
import { NextRequest, NextResponse } from 'next/server'

const API_URL = process.env.DJANGO_API_URL

export async function POST(request: NextRequest) {
  try {
    // Get session cookie
    const cookieStore = await cookies()
    const sessionCookie = cookieStore.get('sessionid')
    if (!sessionCookie) {
      return NextResponse.json(
        { detail: 'Unauthorized' },
        { status: 401 }
      )
    }

    // Get form data
    const formData = await request.formData()
    const resume = formData.get('resume')
    const autoPopulate = formData.get('auto_populate')

    if (!resume) {
      return NextResponse.json(
        { detail: 'No resume file provided' },
        { status: 400 }
      )
    }

    // Forward to Django API
    const djangoFormData = new FormData()
    djangoFormData.append('resume', resume)
    if (autoPopulate) {
      djangoFormData.append('auto_populate', autoPopulate as string)
    }

    const response = await fetch(`${API_URL}/api/v1/candidates/resume/`, {
      method: 'POST',
      headers: {
        Cookie: `sessionid=${sessionCookie.value}`,
      },
      body: djangoFormData,
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status })
    }

    return NextResponse.json(data)
  } catch (error: any) {
    console.error('Resume upload error:', error)
    return NextResponse.json(
      { detail: error.message || 'Failed to upload resume' },
      { status: 500 }
    )
  }
}

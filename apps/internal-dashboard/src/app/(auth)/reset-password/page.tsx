import { ResetPasswordForm } from './reset-password-form'

export const metadata = {
  title: 'Reset Password — HR-Plus',
}

interface PageProps {
  searchParams: Promise<{ token?: string }>
}

export default async function ResetPasswordPage({ searchParams }: PageProps) {
  const params = await searchParams
  const token = params.token

  if (!token) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="w-full max-w-sm space-y-6 px-4">
          <div className="space-y-2 text-center">
            <h1 className="text-2xl font-bold">Invalid Link</h1>
            <p className="text-muted-foreground">
              This password reset link is invalid or has expired.
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="w-full max-w-sm space-y-6 px-4">
        <div className="space-y-2 text-center">
          <h1 className="text-2xl font-bold">Set New Password</h1>
          <p className="text-muted-foreground">Enter your new password below.</p>
        </div>
        <ResetPasswordForm token={token} />
      </div>
    </div>
  )
}

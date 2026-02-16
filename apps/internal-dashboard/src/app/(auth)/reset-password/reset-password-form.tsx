'use client'

import { useActionState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent } from '@/components/ui/card'
import { resetPasswordAction } from './actions'
import { useEffect } from 'react'

interface ResetPasswordFormProps {
  token: string
}

export function ResetPasswordForm({ token }: ResetPasswordFormProps) {
  const router = useRouter()
  const [state, formAction, isPending] = useActionState(resetPasswordAction, null)

  useEffect(() => {
    if (state?.success) {
      // Redirect to login after 2 seconds
      const timeout = setTimeout(() => {
        router.push('/login')
      }, 2000)
      return () => clearTimeout(timeout)
    }
  }, [state?.success, router])

  return (
    <Card>
      <CardContent className="pt-6">
        <form action={formAction} className="space-y-4">
          <input type="hidden" name="token" value={token} />
          {state?.success && (
            <div className="rounded-md bg-green-50 p-3 text-sm text-green-800 border border-green-200">
              Password reset successfully! Redirecting to login...
            </div>
          )}
          {state?.error && (
            <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              {state.error}
            </div>
          )}
          <div className="space-y-2">
            <Label htmlFor="password">New Password</Label>
            <Input
              id="password"
              name="password"
              type="password"
              required
              minLength={8}
              autoComplete="new-password"
              disabled={isPending || state?.success}
            />
            <p className="text-xs text-muted-foreground">
              Password must be at least 8 characters long
            </p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="confirmPassword">Confirm Password</Label>
            <Input
              id="confirmPassword"
              name="confirmPassword"
              type="password"
              required
              minLength={8}
              autoComplete="new-password"
              disabled={isPending || state?.success}
            />
          </div>
          <Button type="submit" className="w-full" disabled={isPending || state?.success}>
            {isPending ? 'Resetting...' : 'Reset Password'}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}

import type { Metadata } from 'next'
import Link from 'next/link'
import { RegisterForm } from './register-form'

export const metadata: Metadata = {
  title: 'Create Account',
  description: 'Create your HR-Plus account to apply for positions and track your applications.',
}

export default function RegisterPage() {
  return (
    <>
      <div className="text-center">
        <h1 className="text-2xl font-bold">Create your account</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Join HR-Plus to discover and apply for opportunities
        </p>
      </div>
      <div className="mt-8">
        <RegisterForm />
      </div>
      <p className="mt-6 text-center text-sm text-muted-foreground">
        Already have an account?{' '}
        <Link href="/login" className="font-medium text-primary hover:text-primary-dark">
          Sign in
        </Link>
      </p>
    </>
  )
}

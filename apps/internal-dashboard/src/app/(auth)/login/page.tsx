import Image from 'next/image'
import { LoginForm } from './login-form'

export const metadata = {
  title: 'Login — Retailability HR',
}

export default function LoginPage() {
  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center bg-gradient-to-br from-slate-50 via-white to-slate-100">
      {/* Subtle background grid */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage:
            'linear-gradient(#000 1px, transparent 1px), linear-gradient(90deg, #000 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }}
      />

      <div className="relative z-10 flex w-full max-w-sm flex-col items-center px-4">
        {/* Logo */}
        <div className="mb-8">
          <Image
            src="/retailability_logo.png"
            alt="Retailability"
            width={200}
            height={68}
            priority
          />
        </div>

        {/* Card */}
        <div className="w-full rounded-2xl border border-slate-200 bg-white px-8 py-10 shadow-xl shadow-slate-200/60">
          <div className="mb-6 text-center">
            <h1 className="text-xl font-semibold tracking-tight text-slate-900">
              Welcome back
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              Sign in to your HR portal
            </p>
          </div>

          <LoginForm />
        </div>

        {/* Powered by */}
        <p className="mt-6 text-[10px] tracking-wide text-slate-400">
          Powered by HR-Plus
        </p>
      </div>
    </div>
  )
}

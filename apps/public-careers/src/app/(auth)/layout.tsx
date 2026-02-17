import Link from 'next/link'
import Image from 'next/image'

export default function AuthLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <div className="flex min-h-[80vh] flex-col items-center justify-center px-6 py-12">
      <Link href="/" className="mb-8">
        <Image
          src="/retailability_logo.png"
          alt="Retailability"
          width={160}
          height={54}
          priority
        />
      </Link>
      <div className="w-full max-w-md">{children}</div>
    </div>
  )
}

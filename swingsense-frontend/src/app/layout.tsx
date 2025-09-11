import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { AuthProvider } from '@/contexts/AuthContext'
import Navbar from '@/components/Navbar'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'SwingSense - AI Golf Coach',
  description: 'Your AI-powered golf coaching companion. Get personalized swing advice, training plans, and resources to improve your game.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>
          <div className="min-h-screen">
            <Navbar />
            <main>
              {children}
            </main>
          </div>
        </AuthProvider>
      </body>
    </html>
  )
}


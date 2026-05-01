'use client'

import { useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { toast } from 'sonner'

interface ErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
  error?: Error
}

export function ErrorBoundary({ children, fallback }: ErrorBoundaryProps) {
  const [state, setState] = useState<ErrorBoundaryState>({ hasError: false })

  useEffect(() => {
    if (state.hasError) {
      toast.error('Something went wrong!', {
        action: {
          label: 'Back to Dashboard',
          onClick: () => window.location.href = '/dashboard',
        },
      })
    }
  }, [state.hasError])

  const handleError = (error: Error) => {
    console.error('ErrorBoundary caught:', error)
    setState({ hasError: true, error })
  }

  if (state.hasError) {
    return fallback || <div>Something went wrong.</div>
  }

  return <>{children}</>
}

import useSWR from 'swr'
import { fetchHealth } from '@/lib/api/health'

export function useHealth() {
  const { data, error, isLoading } = useSWR('/api/health', fetchHealth, {
    refreshInterval: 10000, // 10s poll
  })

  return { data, error, isLoading }
}
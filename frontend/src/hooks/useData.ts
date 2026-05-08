import { useQuery } from '@tanstack/react-query'
import { useAppStore } from '@/store/useAppStore'
import * as api from '@/services/api'

export function useKPIs() {
  const { selectedTeam, selectedMonths } = useAppStore()
  const months = selectedMonths.length ? selectedMonths.join(',') : undefined
  return useQuery({
    queryKey: ['kpis', selectedTeam, months],
    queryFn: () => api.getKPIs(selectedTeam, months),
  })
}

export function useYTDKPIs() {
  const { selectedTeam } = useAppStore()
  return useQuery({
    queryKey: ['ytd-kpis', selectedTeam],
    queryFn: () => api.getYTDKPIs(selectedTeam),
  })
}

export function useMonthlyTrend() {
  const { selectedTeam } = useAppStore()
  return useQuery({
    queryKey: ['monthly-trend', selectedTeam],
    queryFn: () => api.getMonthlyTrend(selectedTeam),
  })
}

export function useDeptComparison() {
  const { selectedMonths } = useAppStore()
  const months = selectedMonths.length ? selectedMonths.join(',') : undefined
  return useQuery({
    queryKey: ['dept-comparison', months],
    queryFn: () => api.getDeptComparison(months),
  })
}

export function useDownloadsVsReuse() {
  const { selectedTeam } = useAppStore()
  return useQuery({
    queryKey: ['downloads-reuse', selectedTeam],
    queryFn: () => api.getDownloadsVsReuse(selectedTeam),
  })
}

export function usePendingTrend() {
  const { selectedTeam } = useAppStore()
  return useQuery({
    queryKey: ['pending-trend', selectedTeam],
    queryFn: () => api.getPendingTrend(selectedTeam),
  })
}

export function useLeaderboard() {
  const { selectedTeam, selectedMonths } = useAppStore()
  const months = selectedMonths.length ? selectedMonths.join(',') : undefined
  return useQuery({
    queryKey: ['leaderboard', selectedTeam, months],
    queryFn: () => api.getLeaderboard(selectedTeam, months),
  })
}

export function useMonths() {
  return useQuery({ queryKey: ['months'], queryFn: api.getMonths })
}

export function useUploadStatus() {
  return useQuery({ queryKey: ['upload-status'], queryFn: api.getUploadStatus })
}

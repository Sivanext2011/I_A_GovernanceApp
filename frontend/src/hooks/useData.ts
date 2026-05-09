import { useQuery } from '@tanstack/react-query'
import { useAppStore } from '@/store/useAppStore'
import * as api from '@/services/api'

function getEffectiveMonths(selected: string[], excluded: string[]): string | undefined {
  if (selected.length > 0) {
    const filtered = selected.filter(m => !excluded.includes(m))
    return filtered.length ? filtered.join(',') : undefined
  }
  if (excluded.length > 0) return undefined // handled via select/filter
  return undefined
}

function filterTrendByExcluded(data: any, excluded: string[]) {
  if (!excluded.length || !data?.months) return data
  const indices = data.months.map((_: string, i: number) => i).filter((i: number) => !excluded.includes(data.months[i]))
  return {
    months: indices.map((i: number) => data.months[i]),
    series: {
      total_savings: indices.map((i: number) => data.series.total_savings[i]),
      automation_savings: indices.map((i: number) => data.series.automation_savings[i]),
      reuse_savings: indices.map((i: number) => data.series.reuse_savings[i]),
      savings_percent: indices.map((i: number) => data.series.savings_percent[i]),
    }
  }
}

function filterMonthlyDataByExcluded(data: any, excluded: string[], keys: string[]) {
  if (!excluded.length || !data?.months) return data
  const indices = data.months.map((_: string, i: number) => i).filter((i: number) => !excluded.includes(data.months[i]))
  const result: any = { months: indices.map((i: number) => data.months[i]) }
  for (const key of keys) {
    result[key] = indices.map((i: number) => data[key][i])
  }
  return result
}

export function useKPIs() {
  const { selectedTeam, selectedMonths, excludedMonths } = useAppStore()
  const months = getEffectiveMonths(selectedMonths, excludedMonths)
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
  const { selectedTeam, excludedMonths } = useAppStore()
  return useQuery({
    queryKey: ['monthly-trend', selectedTeam, excludedMonths],
    queryFn: () => api.getMonthlyTrend(selectedTeam),
    select: (data) => filterTrendByExcluded(data, excludedMonths),
  })
}

export function useDeptComparison() {
  const { selectedMonths, excludedMonths } = useAppStore()
  const months = getEffectiveMonths(selectedMonths, excludedMonths)
  return useQuery({
    queryKey: ['dept-comparison', months],
    queryFn: () => api.getDeptComparison(months),
  })
}

export function useDownloadsVsReuse() {
  const { selectedTeam, excludedMonths } = useAppStore()
  return useQuery({
    queryKey: ['downloads-reuse', selectedTeam, excludedMonths],
    queryFn: () => api.getDownloadsVsReuse(selectedTeam),
    select: (data) => filterMonthlyDataByExcluded(data, excludedMonths, ['downloads', 'reuse']),
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
  const { selectedTeam, selectedMonths, excludedMonths } = useAppStore()
  const months = getEffectiveMonths(selectedMonths, excludedMonths)
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

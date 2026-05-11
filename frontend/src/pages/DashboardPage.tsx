import { Download, TrendingUp, DollarSign, Clock, BarChart3 } from 'lucide-react'
import { KPICard, TeamTabs, MonthMultiSelect, KPISkeleton, EmptyState } from '@/components/ui'
import { MonthlySavingsTrend, SavingsPercentTrend, DepartmentComparison, DownloadsVsReuse, MultiTeamSavingsTrend, MultiTeamSavingsPctTrend } from '@/charts/Charts'
import { LeaderboardGrid } from '@/leaderboard/LeaderboardGrid'
import { useKPIs, useMonthlyTrend, useDeptComparison, useDownloadsVsReuse, useMonths, useTeamStats, useMonthlyTrendAllTeams } from '@/hooks/useData'
import { useUploadStatus } from '@/hooks/useData'
import { useAppStore } from '@/store/useAppStore'
import { useQuery } from '@tanstack/react-query'
import { formatNumber } from '@/lib/utils'

export default function DashboardPage() {
  const { selectedTeam } = useAppStore()
  const { data: uploadStatus } = useUploadStatus()
  const { data: monthsData } = useMonths()
  const { data: kpis, isLoading: kpiLoading } = useKPIs()
  const { data: trend } = useMonthlyTrend()
  const { data: deptComp } = useDeptComparison()
  const { data: dlReuse } = useDownloadsVsReuse()
  const { data: teamStats } = useTeamStats()
  const { data: allTeamsTrend } = useMonthlyTrendAllTeams()

  const hasData = uploadStatus && (uploadStatus.pat || uploadStatus.savings || uploadStatus.download)

  if (!hasData) {
    return <EmptyState title="No Data Loaded" description="Upload PAT, Mapping, Savings, and Download files from the Settings page to get started." />
  }

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <TeamTabs />
        {monthsData && <MonthMultiSelect months={monthsData.months} />}
      </div>

      {/* KPI Cards */}
      {kpiLoading ? <KPISkeleton /> : kpis && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
          <KPICard title="Total Savings" value={kpis.total_savings} icon={DollarSign} gradient="bg-gradient-to-br from-primary-500 to-primary-700" delay={0} />
          <KPICard title="Savings %" value={kpis.savings_percent} icon={TrendingUp} suffix="%" gradient="bg-gradient-to-br from-accent-500 to-accent-700" delay={0.1} />
          <KPICard title="Assets Downloaded" value={kpis.total_downloads} icon={Download} gradient="bg-gradient-to-br from-violet-500 to-violet-700" delay={0.2} />
          <KPICard title="Pending Feedback" value={kpis.pending_feedback} icon={Clock} gradient="bg-gradient-to-br from-rose-500 to-rose-700" delay={0.3} />
          <KPICard title="Billability Hours" value={kpis.billability_hours} icon={BarChart3} gradient="bg-gradient-to-br from-amber-500 to-amber-700" delay={0.4} />
        </div>
      )}

      {/* Team Stats Table (only when Overall) */}
      {selectedTeam === 'Overall' && teamStats && teamStats.length > 0 && (
        <div className="glass-card p-4 overflow-x-auto">
          <h3 className="text-sm font-semibold mb-3">Team-wise Statistics</h3>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-[var(--text-secondary)] border-b border-[var(--border)]">
                <th className="pb-2 pr-4">Team</th>
                <th className="pb-2 pr-4 text-right">Total Savings</th>
                <th className="pb-2 pr-4 text-right">Savings %</th>
                <th className="pb-2 pr-4 text-right">Downloads</th>
                <th className="pb-2 pr-4 text-right">Pending</th>
                <th className="pb-2 text-right">Billability</th>
              </tr>
            </thead>
            <tbody>
              {teamStats.map((s: any) => (
                <tr key={s.team} className="border-b border-[var(--border)]">
                  <td className="py-2 pr-4 font-medium">{s.team}</td>
                  <td className="py-2 pr-4 text-right">{formatNumber(s.total_savings)}</td>
                  <td className="py-2 pr-4 text-right">{s.savings_percent != null ? `${s.savings_percent}%` : 'N/A'}</td>
                  <td className="py-2 pr-4 text-right">{s.total_downloads}</td>
                  <td className="py-2 pr-4 text-right">{s.pending_feedback}</td>
                  <td className="py-2 text-right">{formatNumber(s.billability_hours)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Charts - 1 per row */}
      <div className="grid grid-cols-1 gap-6">
        {selectedTeam === 'Overall' && allTeamsTrend ? (
          <>
            <MultiTeamSavingsTrend months={allTeamsTrend.months} teams={allTeamsTrend.teams} />
            <MultiTeamSavingsPctTrend months={allTeamsTrend.months} teams={allTeamsTrend.teams} />
          </>
        ) : (
          <>
            {trend && <MonthlySavingsTrend months={trend.months} series={trend.series} />}
            {trend && <SavingsPercentTrend months={trend.months} values={trend.series.savings_percent} />}
          </>
        )}
        {selectedTeam === 'Overall' && deptComp && deptComp.teams?.length > 0 && <DepartmentComparison teams={deptComp.teams} total_savings={deptComp.total_savings} savings_percent={deptComp.savings_percent} />}
        {dlReuse && <DownloadsVsReuse months={dlReuse.months} downloads={dlReuse.downloads} reuse={dlReuse.reuse} />}
      </div>

      {/* Leaderboard */}
      <div className="glass-card p-6">
        <h3 className="text-lg font-semibold mb-4">Top Practitioners</h3>
        <LeaderboardGrid />
      </div>
    </div>
  )
}

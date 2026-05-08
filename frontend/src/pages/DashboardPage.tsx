import { Download, TrendingUp, DollarSign, Clock, BarChart3 } from 'lucide-react'
import { KPICard, TeamTabs, MonthMultiSelect, KPISkeleton, EmptyState } from '@/components/ui'
import { MonthlySavingsTrend, SavingsPercentTrend, DepartmentComparison, DownloadsVsReuse } from '@/charts/Charts'
import { LeaderboardGrid } from '@/leaderboard/LeaderboardGrid'
import { useKPIs, useMonthlyTrend, useDeptComparison, useDownloadsVsReuse, useMonths } from '@/hooks/useData'
import { useUploadStatus } from '@/hooks/useData'

export default function DashboardPage() {
  const { data: uploadStatus } = useUploadStatus()
  const { data: monthsData } = useMonths()
  const { data: kpis, isLoading: kpiLoading } = useKPIs()
  const { data: trend } = useMonthlyTrend()
  const { data: deptComp } = useDeptComparison()
  const { data: dlReuse } = useDownloadsVsReuse()

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

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {trend && <MonthlySavingsTrend months={trend.months} series={trend.series} />}
        {trend && <SavingsPercentTrend months={trend.months} values={trend.series.savings_percent} />}
        {deptComp && <DepartmentComparison teams={deptComp.teams} total_savings={deptComp.total_savings} savings_percent={deptComp.savings_percent} />}
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

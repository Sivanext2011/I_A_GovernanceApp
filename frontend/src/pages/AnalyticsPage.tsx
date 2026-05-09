import { BarChart3, Download, TrendingUp, DollarSign, Clock, Save } from 'lucide-react'
import { KPICard, TeamTabs, MonthMultiSelect, KPISkeleton } from '@/components/ui'
import { MonthlySavingsTrend, SavingsPercentTrend, DepartmentComparison, DownloadsVsReuse, PendingFeedbackChart } from '@/charts/Charts'
import { useYTDKPIs, useMonthlyTrend, useDeptComparison, useDownloadsVsReuse, usePendingTrend, useMonths } from '@/hooks/useData'
import { recordPendingTrend } from '@/services/api'
import { useAppStore } from '@/store/useAppStore'
import { useMutation, useQueryClient } from '@tanstack/react-query'

export default function AnalyticsPage() {
  const { data: monthsData } = useMonths()
  const { selectedTeam } = useAppStore()
  const { data: ytd, isLoading } = useYTDKPIs()
  const { data: trend } = useMonthlyTrend()
  const { data: deptComp } = useDeptComparison()
  const { data: dlReuse } = useDownloadsVsReuse()
  const { data: pendingTrend } = usePendingTrend()
  const queryClient = useQueryClient()

  const recordMutation = useMutation({
    mutationFn: () => recordPendingTrend(selectedTeam),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-trend'] })
      alert('Pending feedback count recorded for this month')
    },
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-2">
        <BarChart3 className="w-6 h-6 text-primary-500" />
        <h2 className="text-xl font-bold">Monetization Analytics Dashboard</h2>
      </div>

      <TeamTabs />
      {monthsData && <MonthMultiSelect months={monthsData.months} />}

      {/* YTD KPIs */}
      {isLoading ? <KPISkeleton /> : ytd && (
        <>
          <h3 className="text-sm font-semibold text-[var(--text-secondary)] uppercase tracking-wide">Year-to-Date</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
            <KPICard title="YTD Total Savings" value={ytd.ytd.total_savings} icon={DollarSign} gradient="bg-gradient-to-br from-primary-500 to-primary-700" />
            <KPICard title="YTD Savings %" value={ytd.ytd.savings_percent} icon={TrendingUp} suffix="%" gradient="bg-gradient-to-br from-accent-500 to-accent-700" delay={0.1} />
            <KPICard title="YTD Downloads" value={ytd.ytd.total_downloads} icon={Download} gradient="bg-gradient-to-br from-violet-500 to-violet-700" delay={0.2} />
            <KPICard title="Pending Feedback" value={ytd.ytd.pending_feedback} icon={Clock} gradient="bg-gradient-to-br from-rose-500 to-rose-700" delay={0.3} />
            <KPICard title="YTD Billability" value={ytd.ytd.billability_hours} icon={BarChart3} gradient="bg-gradient-to-br from-amber-500 to-amber-700" delay={0.4} />
          </div>
        </>
      )}

      {/* All Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {trend && <MonthlySavingsTrend months={trend.months} series={trend.series} />}
        {trend && <SavingsPercentTrend months={trend.months} values={trend.series.savings_percent} />}
        {deptComp && <DepartmentComparison teams={deptComp.teams} total_savings={deptComp.total_savings} savings_percent={deptComp.savings_percent} />}
        {dlReuse && <DownloadsVsReuse months={dlReuse.months} downloads={dlReuse.downloads} reuse={dlReuse.reuse} />}
        {pendingTrend && <PendingFeedbackChart months={pendingTrend.months} pending={pendingTrend.pending} />}
      </div>

      {/* Record pending feedback snapshot */}
      <div className="flex justify-end">
        <button
          onClick={() => recordMutation.mutate()}
          disabled={recordMutation.isPending}
          className="btn-secondary flex items-center gap-2 text-sm"
        >
          <Save className="w-4 h-4" />
          {recordMutation.isPending ? 'Recording...' : 'Record Pending Feedback Count'}
        </button>
      </div>
    </div>
  )
}

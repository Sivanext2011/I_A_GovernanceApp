import Plot from 'react-plotly.js'
import { useAppStore } from '@/store/useAppStore'

const darkLayout = {
  paper_bgcolor: 'rgba(0,0,0,0)',
  plot_bgcolor: 'rgba(0,0,0,0)',
  font: { color: '#94a3b8' },
  xaxis: { gridcolor: '#334155' },
  yaxis: { gridcolor: '#334155' },
}

const lightLayout = {
  paper_bgcolor: 'rgba(0,0,0,0)',
  plot_bgcolor: 'rgba(0,0,0,0)',
  font: { color: '#475569' },
  xaxis: { gridcolor: '#e2e8f0' },
  yaxis: { gridcolor: '#e2e8f0' },
}

function useChartTheme() {
  const { darkMode } = useAppStore()
  return darkMode ? darkLayout : lightLayout
}

interface TrendChartProps {
  months: string[]
  series: { total_savings: number[]; automation_savings: number[]; reuse_savings: number[] }
}

export function MonthlySavingsTrend({ months, series }: TrendChartProps) {
  const theme = useChartTheme()
  return (
    <div className="glass-card p-4">
      <h3 className="text-sm font-semibold mb-2">Monthly Savings Trend</h3>
      <Plot
        data={[
          { x: months, y: series.total_savings, type: 'bar', name: 'Total', marker: { color: '#3b82f6' } },
          { x: months, y: series.automation_savings, type: 'bar', name: 'Automation', marker: { color: '#14b8a6' } },
          { x: months, y: series.reuse_savings, type: 'bar', name: 'Reuse', marker: { color: '#f59e0b' } },
        ]}
        layout={{ ...theme, margin: { t: 20, r: 20, b: 40, l: 60 }, legend: { orientation: 'h', y: -0.2 }, barmode: 'group', autosize: true }}
        config={{ responsive: true, displayModeBar: false }}
        className="w-full"
        style={{ width: '100%', height: '300px' }}
      />
    </div>
  )
}

interface SavingsPctProps {
  months: string[]
  values: number[]
}

export function SavingsPercentTrend({ months, values }: SavingsPctProps) {
  const theme = useChartTheme()
  return (
    <div className="glass-card p-4">
      <h3 className="text-sm font-semibold mb-2">Savings % Trend</h3>
      <Plot
        data={[{ x: months, y: values, type: 'bar', marker: { color: '#8b5cf6' } }]}
        layout={{ ...theme, margin: { t: 20, r: 20, b: 40, l: 60 }, yaxis: { ...theme.yaxis, title: { text: '%' } }, autosize: true }}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: '100%', height: '300px' }}
      />
    </div>
  )
}

interface DeptCompProps {
  teams: string[]
  total_savings: number[]
  savings_percent: number[]
}

export function DepartmentComparison({ teams, total_savings, savings_percent }: DeptCompProps) {
  const theme = useChartTheme()
  if (!teams || teams.length === 0) return null
  return (
    <div className="glass-card p-4">
      <h3 className="text-sm font-semibold mb-2">Department wise Savings</h3>
      <Plot
        data={[
          { x: teams, y: total_savings, type: 'bar', name: 'Total Savings', marker: { color: '#3b82f6' } },
          { x: teams, y: savings_percent, type: 'scatter', mode: 'lines+markers', name: 'Savings %', yaxis: 'y2', line: { color: '#ef4444', width: 2 } },
        ]}
        layout={{ ...theme, margin: { t: 20, r: 60, b: 40, l: 60 }, xaxis: { ...theme.xaxis, type: 'category' }, yaxis2: { overlaying: 'y', side: 'right', title: { text: '%' }, gridcolor: 'transparent' }, barmode: 'group', autosize: true }}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: '100%', height: '300px' }}
      />
    </div>
  )
}

interface DlReuse {
  months: string[]
  downloads: number[]
  reuse: number[]
}

export function DownloadsVsReuse({ months, downloads, reuse }: DlReuse) {
  const theme = useChartTheme()
  return (
    <div className="glass-card p-4">
      <h3 className="text-sm font-semibold mb-2">Downloads vs Reuse</h3>
      <Plot
        data={[
          { x: months, y: downloads, type: 'bar', name: 'Downloads', marker: { color: '#06b6d4' } },
          { x: months, y: reuse, type: 'bar', name: 'Reused with Savings', marker: { color: '#10b981' } },
        ]}
        layout={{ ...theme, margin: { t: 20, r: 20, b: 40, l: 60 }, barmode: 'group', autosize: true }}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: '100%', height: '300px' }}
      />
    </div>
  )
}

interface PendingProps {
  months: string[]
  pending: (number | null)[]
}

export function PendingFeedbackChart({ months, pending }: PendingProps) {
  const theme = useChartTheme()
  return (
    <div className="glass-card p-4">
      <h3 className="text-sm font-semibold mb-2">Pending Feedback</h3>
      <Plot
        data={[{ x: months, y: pending, type: 'bar', marker: { color: '#f43f5e' } }]}
        layout={{ ...theme, margin: { t: 20, r: 20, b: 40, l: 60 }, autosize: true }}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: '100%', height: '300px' }}
      />
    </div>
  )
}

interface MultiTeamTrendProps {
  months: string[]
  teams: Record<string, { total_savings: number[]; savings_percent: number[] }>
}

const TEAM_COLORS: Record<string, string> = {
  'Overall': '#3b82f6',
  'Billing': '#14b8a6',
  'Charging': '#f59e0b',
  'SDC Billing&MW': '#8b5cf6',
  'SDC CS&DFE': '#ef4444',
}

export function MultiTeamSavingsTrend({ months, teams }: MultiTeamTrendProps) {
  const theme = useChartTheme()
  const data = Object.entries(teams).map(([team, series]) => ({
    x: months, y: series.total_savings, type: 'bar' as const, name: team,
    marker: { color: TEAM_COLORS[team] || '#6b7280' },
  }))
  return (
    <div className="glass-card p-4">
      <h3 className="text-sm font-semibold mb-2">Monthly Savings Trend (All Teams)</h3>
      <Plot
        data={data}
        layout={{ ...theme, margin: { t: 20, r: 20, b: 40, l: 60 }, legend: { orientation: 'h', y: -0.2 }, barmode: 'group', autosize: true }}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: '100%', height: '350px' }}
      />
    </div>
  )
}

export function MultiTeamSavingsPctTrend({ months, teams }: MultiTeamTrendProps) {
  const theme = useChartTheme()
  const data = Object.entries(teams).map(([team, series]) => ({
    x: months, y: series.savings_percent, type: 'bar' as const, name: team,
    marker: { color: TEAM_COLORS[team] || '#6b7280' },
  }))
  return (
    <div className="glass-card p-4">
      <h3 className="text-sm font-semibold mb-2">Savings % Trend (All Teams)</h3>
      <Plot
        data={data}
        layout={{ ...theme, margin: { t: 20, r: 20, b: 40, l: 60 }, yaxis: { ...theme.yaxis, title: { text: '%' } }, legend: { orientation: 'h', y: -0.2 }, barmode: 'group', autosize: true }}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: '100%', height: '350px' }}
      />
    </div>
  )
}

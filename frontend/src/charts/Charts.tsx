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
          { x: months, y: series.total_savings, type: 'scatter', mode: 'lines+markers', name: 'Total', line: { color: '#3b82f6', width: 3 } },
          { x: months, y: series.automation_savings, type: 'scatter', mode: 'lines+markers', name: 'Automation', line: { color: '#14b8a6', width: 2 } },
          { x: months, y: series.reuse_savings, type: 'scatter', mode: 'lines+markers', name: 'Reuse', line: { color: '#f59e0b', width: 2 } },
        ]}
        layout={{ ...theme, margin: { t: 20, r: 20, b: 40, l: 60 }, legend: { orientation: 'h', y: -0.2 }, autosize: true }}
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
        data={[{ x: months, y: values, type: 'scatter', mode: 'lines+markers', fill: 'tozeroy', line: { color: '#8b5cf6', width: 3 }, fillcolor: 'rgba(139,92,246,0.1)' }]}
        layout={{ ...theme, margin: { t: 20, r: 20, b: 40, l: 60 }, yaxis: { ...theme.yaxis, title: '%' }, autosize: true }}
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
    <div className="glass-card p-4 lg:col-span-2">
      <h3 className="text-sm font-semibold mb-2">Department Comparison</h3>
      <Plot
        data={[
          { x: teams, y: total_savings, type: 'bar', name: 'Total Savings', marker: { color: '#3b82f6' } },
          { x: teams, y: savings_percent, type: 'scatter', mode: 'lines+markers', name: 'Savings %', yaxis: 'y2', line: { color: '#ef4444', width: 2 } },
        ]}
        layout={{ ...theme, margin: { t: 20, r: 60, b: 40, l: 60 }, yaxis2: { overlaying: 'y', side: 'right', title: '%', gridcolor: 'transparent' }, barmode: 'group', autosize: true }}
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

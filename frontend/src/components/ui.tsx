import { motion } from 'framer-motion'
import { LucideIcon } from 'lucide-react'
import { cn, formatNumber } from '@/lib/utils'
import { useAppStore } from '@/store/useAppStore'

// KPI Card
interface KPICardProps {
  title: string
  value: number | null | undefined
  icon: LucideIcon
  suffix?: string
  gradient: string
  delay?: number
}

export function KPICard({ title, value, icon: Icon, suffix = '', gradient, delay = 0 }: KPICardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.4 }}
      className="kpi-card relative overflow-hidden"
    >
      <div className={cn('absolute top-0 right-0 w-24 h-24 rounded-bl-full opacity-20', gradient)} />
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-[var(--text-secondary)] mb-1">{title}</p>
          <p className="text-2xl font-bold">
            {value != null ? formatNumber(value) : 'N/A'}
            {suffix && value != null && <span className="text-sm font-normal ml-1">{suffix}</span>}
          </p>
        </div>
        <div className={cn('w-12 h-12 rounded-xl flex items-center justify-center', gradient)}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </motion.div>
  )
}

// Team Tabs
const TEAMS = ['Overall', 'Billing', 'Charging', 'SDC Billing&MW', 'SDC CS&DFE']

export function TeamTabs() {
  const { selectedTeam, setTeam } = useAppStore()
  return (
    <div className="flex flex-wrap gap-2 mb-6">
      {TEAMS.map((team) => (
        <button
          key={team}
          onClick={() => setTeam(team)}
          className={cn('team-tab', selectedTeam === team ? 'team-tab-active' : 'team-tab-inactive')}
        >
          {team}
        </button>
      ))}
    </div>
  )
}

// Loading Skeleton
export function Skeleton({ className }: { className?: string }) {
  return <div className={cn('animate-pulse bg-slate-200 dark:bg-slate-700 rounded', className)} />
}

export function KPISkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-4">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="kpi-card">
          <Skeleton className="h-4 w-24 mb-3" />
          <Skeleton className="h-8 w-32" />
        </div>
      ))}
    </div>
  )
}

// Empty State
export function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex flex-col items-center justify-center py-16 text-center"
    >
      <div className="w-20 h-20 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-4">
        <svg className="w-10 h-10 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
        </svg>
      </div>
      <h3 className="text-lg font-semibold mb-1">{title}</h3>
      <p className="text-[var(--text-secondary)] max-w-sm">{description}</p>
    </motion.div>
  )
}

// Error State
export function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mb-4">
        <svg className="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
      </div>
      <p className="text-red-600 dark:text-red-400 font-medium">{message}</p>
    </div>
  )
}

// Month Multi-Select
interface MonthSelectProps {
  months: string[]
}

export function MonthMultiSelect({ months }: MonthSelectProps) {
  const { selectedMonths, setMonths, excludedMonths, setExcludedMonths } = useAppStore()

  const toggle = (m: string) => {
    setMonths(selectedMonths.includes(m) ? [] : [m])
    // Remove from excluded if selecting
    if (excludedMonths.includes(m)) setExcludedMonths(excludedMonths.filter(x => x !== m))
  }

  const toggleExclude = (m: string) => {
    setExcludedMonths(excludedMonths.includes(m) ? excludedMonths.filter(x => x !== m) : [...excludedMonths, m])
    // Remove from selected if excluding
    if (selectedMonths.includes(m)) setMonths(selectedMonths.filter(x => x !== m))
  }

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => { setMonths([]); setExcludedMonths([]) }}
          className={cn('team-tab text-xs', selectedMonths.length === 0 && excludedMonths.length === 0 ? 'team-tab-active' : 'team-tab-inactive')}
        >
          All
        </button>
        {months.map((m) => (
          <button
            key={m}
            onClick={() => toggle(m)}
            className={cn('team-tab text-xs', selectedMonths.includes(m) ? 'team-tab-active' : excludedMonths.includes(m) ? 'team-tab-excluded' : 'team-tab-inactive')}
          >
            {m}
          </button>
        ))}
      </div>
      <div className="flex flex-wrap gap-2 items-center">
        <span className="text-xs text-[var(--text-secondary)]">Exclude:</span>
        {months.map((m) => (
          <button
            key={m}
            onClick={() => toggleExclude(m)}
            className={cn('text-xs px-2 py-0.5 rounded', excludedMonths.includes(m) ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' : 'bg-slate-100 dark:bg-slate-800 text-[var(--text-secondary)]')}
          >
            {excludedMonths.includes(m) ? '✕ ' : ''}{m}
          </button>
        ))}
      </div>
    </div>
  )
}

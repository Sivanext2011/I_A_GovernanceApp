import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { AlertTriangle, Mail } from 'lucide-react'
import { useAppStore } from '@/store/useAppStore'
import { getMissingSavings, sendMail } from '@/services/api'
import { TeamTabs, EmptyState, Skeleton } from '@/components/ui'
import { useMonths } from '@/hooks/useData'
import { useState } from 'react'
import { cn } from '@/lib/utils'

function MonthSelector({ label, months, selected, onChange }: { label: string; months: string[]; selected: string[]; onChange: (m: string[]) => void }) {
  const toggle = (m: string) => {
    onChange(selected.includes(m) ? selected.filter(x => x !== m) : [...selected, m])
  }
  return (
    <div>
      <p className="text-xs font-medium text-[var(--text-secondary)] mb-1">{label}</p>
      <div className="flex flex-wrap gap-2">
        <button onClick={() => onChange([])} className={cn('team-tab text-xs', selected.length === 0 ? 'team-tab-active' : 'team-tab-inactive')}>All</button>
        {months.map((m) => (
          <button key={m} onClick={() => toggle(m)} className={cn('team-tab text-xs', selected.includes(m) ? 'team-tab-active' : 'team-tab-inactive')}>{m}</button>
        ))}
      </div>
    </div>
  )
}

export default function MissingSavingsPage() {
  const { selectedTeam } = useAppStore()
  const { data: monthsData } = useMonths()
  const [patMonths, setPatMonths] = useState<string[]>([])
  const [savingsMonths, setSavingsMonths] = useState<string[]>([])

  const patMonthsParam = patMonths.length ? patMonths.join(',') : undefined
  const savingsMonthsParam = savingsMonths.length ? savingsMonths.join(',') : undefined

  const { data, isLoading } = useQuery({
    queryKey: ['missing-savings', selectedTeam, patMonthsParam, savingsMonthsParam],
    queryFn: () => getMissingSavings(selectedTeam, patMonthsParam, savingsMonthsParam),
  })

  const [sending, setSending] = useState<string | null>(null)

  const handleSendReminder = async (email: string, name: string) => {
    if (!email) return
    setSending(email)
    try {
      await sendMail({
        recipients: [email],
        subject: 'Action Required: Missing Savings Submission',
        body: `<p>Dear ${name},</p><p>Our records indicate that you have automation-assisted PAT activities but have not submitted corresponding savings. Please submit your savings at your earliest convenience.</p><p>Best regards,<br/>Automation Governance Team</p>`,
      })
      alert('Reminder sent successfully')
    } catch {
      alert('Failed to send reminder. Please ensure you are authenticated.')
    }
    setSending(null)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-2">
        <AlertTriangle className="w-6 h-6 text-amber-500" />
        <h2 className="text-xl font-bold">Missing Savings Governance</h2>
      </div>

      <TeamTabs />

      {monthsData && (
        <div className="space-y-3">
          <MonthSelector label="PAT Months (activity period)" months={monthsData.months} selected={patMonths} onChange={setPatMonths} />
          <MonthSelector label="Savings Months (recording period)" months={monthsData.months} selected={savingsMonths} onChange={setSavingsMonths} />
        </div>
      )}

      {isLoading ? (
        <div className="space-y-3">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-16 w-full" />)}</div>
      ) : !data || data.count === 0 ? (
        <EmptyState title="All Compliant" description="No practitioners with missing savings found for the selected filters." />
      ) : (
        <div className="space-y-3">
          <p className="text-sm text-[var(--text-secondary)]">{data.count} non-compliant practitioners found</p>
          {data.records.map((rec: any, idx: number) => (
            <motion.div
              key={rec.signum}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.05 }}
              className="glass-card p-4 flex items-center justify-between"
            >
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                  <AlertTriangle className="w-5 h-5 text-amber-600" />
                </div>
                <div>
                  <p className="font-medium">{rec.name}</p>
                  <p className="text-xs text-[var(--text-secondary)]">{rec.email} • {rec.department}</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <p className="text-sm font-medium">{rec.pat_count} PATs</p>
                  <p className="text-xs text-red-500">Savings: {rec.total_savings}</p>
                </div>
                <button
                  onClick={() => handleSendReminder(rec.email, rec.name)}
                  disabled={sending === rec.email}
                  className="btn-primary flex items-center gap-2 text-sm"
                >
                  <Mail className="w-4 h-4" />
                  {sending === rec.email ? 'Sending...' : 'Remind'}
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}

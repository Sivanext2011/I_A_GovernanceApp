import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { AlertTriangle, Mail, Eye, Send, CheckSquare, Square, ArrowUpCircle, ChevronDown, ChevronRight, Trash2 } from 'lucide-react'
import { useAppStore } from '@/store/useAppStore'
import { getMissingSavings, previewMissingSavingsMail, sendMissingSavingsMail, escalateToManager, excludePatRecords } from '@/services/api'
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

interface MailPreview {
  signum: string; name: string; email: string; subject: string; body: string; pat_count: number
}

export default function MissingSavingsPage() {
  const { selectedTeam } = useAppStore()
  const { data: monthsData } = useMonths()
  const [patMonths, setPatMonths] = useState<string[]>([])
  const [savingsMonths, setSavingsMonths] = useState<string[]>([])
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [expanded, setExpanded] = useState<Set<string>>(new Set())
  const [previews, setPreviews] = useState<MailPreview[] | null>(null)
  const [showPreview, setShowPreview] = useState(false)
  const queryClient = useQueryClient()

  const patMonthsParam = patMonths.length ? patMonths.join(',') : undefined
  const savingsMonthsParam = savingsMonths.length ? savingsMonths.join(',') : undefined

  const { data, isLoading } = useQuery({
    queryKey: ['missing-savings', selectedTeam, patMonthsParam, savingsMonthsParam],
    queryFn: () => getMissingSavings(selectedTeam, patMonthsParam, savingsMonthsParam),
  })

  const records: any[] = data?.records || []

  const toggleSelect = (signum: string) => {
    const next = new Set(selected)
    next.has(signum) ? next.delete(signum) : next.add(signum)
    setSelected(next)
  }

  const toggleSelectAll = () => {
    if (selected.size === records.length) setSelected(new Set())
    else setSelected(new Set(records.map((r: any) => r.signum)))
  }

  const toggleExpand = (signum: string) => {
    const next = new Set(expanded)
    next.has(signum) ? next.delete(signum) : next.add(signum)
    setExpanded(next)
  }

  const previewMutation = useMutation({
    mutationFn: () => previewMissingSavingsMail(Array.from(selected), selectedTeam, patMonths, savingsMonths),
    onSuccess: (res) => { setPreviews(res.previews); setShowPreview(true) },
  })

  const sendMutation = useMutation({
    mutationFn: () => sendMissingSavingsMail(Array.from(selected), selectedTeam, patMonths, savingsMonths),
    onSuccess: (res) => {
      const sent = res.results.filter((r: any) => r.sent).length
      alert(`Sent: ${sent}, Failed: ${res.results.length - sent}`)
      setShowPreview(false)
    },
    onError: () => alert('Failed to send. Check authentication.'),
  })

  const escalateMutation = useMutation({
    mutationFn: () => escalateToManager(Array.from(selected), 'missing_savings'),
    onSuccess: (res) => {
      const sent = res.results.filter((r: any) => r.sent).length
      alert(`Escalation sent to ${sent} manager(s)`)
    },
    onError: () => alert('Escalation failed. Check authentication.'),
  })

  const excludeMutation = useMutation({
    mutationFn: (patIds: string[]) => excludePatRecords(patIds),
    onSuccess: (res) => {
      alert(`Removed ${res.removed} PAT records`)
      queryClient.invalidateQueries({ queryKey: ['missing-savings'] })
    },
  })

  const handleExcludePat = (patId: string) => {
    if (confirm(`Exclude PAT ID ${patId} from dataset?`)) {
      excludeMutation.mutate([patId])
    }
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
        <div className="space-y-4">
          {/* Action bar */}
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div className="flex items-center gap-4">
              <button onClick={toggleSelectAll} className="flex items-center gap-2 text-sm font-medium hover:text-blue-600">
                {selected.size === records.length ? <CheckSquare className="w-4 h-4" /> : <Square className="w-4 h-4" />}
                {selected.size === records.length ? 'Deselect All' : 'Select All'}
              </button>
              <span className="text-sm text-[var(--text-secondary)]">
                {data.count} non-compliant{selected.size > 0 && ` • ${selected.size} selected`}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button onClick={() => previewMutation.mutate()} disabled={selected.size === 0 || previewMutation.isPending} className="btn-secondary flex items-center gap-2 text-sm disabled:opacity-50">
                <Eye className="w-4 h-4" /> Preview
              </button>
              <button onClick={() => sendMutation.mutate()} disabled={selected.size === 0 || sendMutation.isPending} className="btn-primary flex items-center gap-2 text-sm disabled:opacity-50">
                <Send className="w-4 h-4" /> {sendMutation.isPending ? 'Sending...' : `Send (${selected.size})`}
              </button>
              <button onClick={() => escalateMutation.mutate()} disabled={selected.size === 0 || escalateMutation.isPending} className="btn-danger flex items-center gap-2 text-sm disabled:opacity-50">
                <ArrowUpCircle className="w-4 h-4" /> {escalateMutation.isPending ? 'Escalating...' : 'Escalate'}
              </button>
            </div>
          </div>

          {/* Collapsible Records */}
          {records.map((rec: any, idx: number) => {
            const isExpanded = expanded.has(rec.signum)
            return (
              <motion.div
                key={rec.signum}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.03 }}
                className="glass-card overflow-hidden"
              >
                <div className="p-4 flex items-center justify-between cursor-pointer" onClick={() => toggleExpand(rec.signum)}>
                  <div className="flex items-center gap-3">
                    <button onClick={(e) => { e.stopPropagation(); toggleSelect(rec.signum) }} className="hover:text-blue-600">
                      {selected.has(rec.signum) ? <CheckSquare className="w-5 h-5 text-blue-600" /> : <Square className="w-5 h-5" />}
                    </button>
                    <div className="w-9 h-9 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                      <AlertTriangle className="w-4 h-4 text-amber-600" />
                    </div>
                    <div>
                      <p className="font-medium text-sm">{rec.name}</p>
                      <p className="text-xs text-[var(--text-secondary)]">{rec.email} • {rec.department}</p>
                      {rec.manager_email && <p className="text-xs text-[var(--text-secondary)]">Manager CC: {rec.manager_email}</p>}
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <p className="text-sm font-medium">{rec.pat_count} PATs</p>
                      <p className="text-xs text-red-500">Savings: {rec.total_savings}</p>
                    </div>
                    {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                  </div>
                </div>

                {isExpanded && rec.pat_activities && rec.pat_activities.length > 0 && (
                  <div className="border-t border-[var(--border)] px-4 pb-4">
                    <table className="w-full text-xs mt-3">
                      <thead>
                        <tr className="text-left text-[var(--text-secondary)]">
                          <th className="pb-2">PAT ID</th>
                          <th className="pb-2">Activity Name</th>
                          <th className="pb-2">Start Date & Time</th>
                          <th className="pb-2">End Date & Time</th>
                          <th className="pb-2">Status</th>
                          <th className="pb-2"></th>
                        </tr>
                      </thead>
                      <tbody>
                        {rec.pat_activities.map((act: any, i: number) => (
                          <tr key={i} className="border-t border-[var(--border)]">
                            <td className="py-2">{act.pat_id}</td>
                            <td className="py-2">{act.activity_name}</td>
                            <td className="py-2">{act.start_date}</td>
                            <td className="py-2">{act.end_date}</td>
                            <td className="py-2">{act.status}</td>
                            <td className="py-2">
                              <button onClick={() => handleExcludePat(act.pat_id)} className="text-red-500 hover:text-red-700" title="Exclude this record">
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </motion.div>
            )
          })}

          {/* Preview Modal */}
          {showPreview && previews && (
            <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={() => setShowPreview(false)}>
              <div className="bg-[var(--bg-primary)] rounded-xl max-w-3xl w-full max-h-[80vh] overflow-y-auto p-6 space-y-4" onClick={(e) => e.stopPropagation()}>
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-bold">Mail Preview ({previews.length} mails)</h3>
                  <button onClick={() => setShowPreview(false)} className="text-sm hover:text-rose-500">Close</button>
                </div>
                {previews.map((p) => (
                  <div key={p.signum} className="border border-[var(--border)] rounded-lg p-4 space-y-2">
                    <p className="text-sm"><strong>To:</strong> {p.name} ({p.email})</p>
                    <p className="text-sm"><strong>Subject:</strong> {p.subject}</p>
                    <div className="text-xs border-t pt-2 mt-2" dangerouslySetInnerHTML={{ __html: p.body }} />
                  </div>
                ))}
                <div className="flex justify-end gap-2 pt-2">
                  <button onClick={() => setShowPreview(false)} className="btn-secondary text-sm">Cancel</button>
                  <button onClick={() => sendMutation.mutate()} disabled={sendMutation.isPending} className="btn-primary flex items-center gap-2 text-sm">
                    <Mail className="w-4 h-4" /> {sendMutation.isPending ? 'Sending...' : 'Send All'}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

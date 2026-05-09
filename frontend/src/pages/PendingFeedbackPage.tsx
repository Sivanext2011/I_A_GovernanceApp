import { useQuery, useMutation } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Clock, Mail, Eye, Send, CheckSquare, Square, ChevronDown, ChevronRight, ArrowUpCircle } from 'lucide-react'
import { useAppStore } from '@/store/useAppStore'
import { getPendingFeedback, previewPendingFeedbackMail, sendPendingFeedbackMail, escalateToManager } from '@/services/api'
import { TeamTabs, EmptyState, Skeleton } from '@/components/ui'
import { useState, useMemo } from 'react'

interface FeedbackRecord {
  feedback_id: string
  asset_registry_id: string
  asset_name: string
  signum: string
  name: string
  email: string
  department: string
  download_date: string
  due_date: string
  overdue_duration: number
}

interface MailPreview {
  signum: string
  name: string
  email: string
  subject: string
  body: string
  item_count: number
}

export default function PendingFeedbackPage() {
  const { selectedTeam } = useAppStore()
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [expanded, setExpanded] = useState<Set<string>>(new Set())
  const [previews, setPreviews] = useState<MailPreview[] | null>(null)
  const [showPreview, setShowPreview] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['pending-feedback', selectedTeam],
    queryFn: () => getPendingFeedback(selectedTeam),
  })

  const grouped = useMemo(() => {
    if (!data?.records) return {}
    const map: Record<string, FeedbackRecord[]> = {}
    for (const rec of data.records) {
      if (!map[rec.signum]) map[rec.signum] = []
      map[rec.signum].push(rec)
    }
    return map
  }, [data])

  const practitioners = useMemo(() => Object.keys(grouped), [grouped])

  const toggleSelect = (signum: string) => {
    const next = new Set(selected)
    next.has(signum) ? next.delete(signum) : next.add(signum)
    setSelected(next)
  }

  const toggleSelectAll = () => {
    if (selected.size === practitioners.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(practitioners))
    }
  }

  const toggleExpand = (signum: string) => {
    const next = new Set(expanded)
    next.has(signum) ? next.delete(signum) : next.add(signum)
    setExpanded(next)
  }

  const previewMutation = useMutation({
    mutationFn: () => previewPendingFeedbackMail(Array.from(selected), selectedTeam),
    onSuccess: (res) => {
      setPreviews(res.previews)
      setShowPreview(true)
    },
  })

  const sendMutation = useMutation({
    mutationFn: () => sendPendingFeedbackMail(Array.from(selected), selectedTeam),
    onSuccess: (res) => {
      const sent = res.results.filter((r: any) => r.sent).length
      const failed = res.results.length - sent
      alert(`Sent: ${sent}, Failed: ${failed}`)
      setShowPreview(false)
    },
    onError: () => alert('Failed to send mails. Check authentication.'),
  })

  const escalateMutation = useMutation({
    mutationFn: () => escalateToManager(Array.from(selected), 'pending_feedback'),
    onSuccess: (res) => {
      const sent = res.results.filter((r: any) => r.sent).length
      alert(`Escalation sent to ${sent} manager(s)`)
    },
    onError: () => alert('Escalation failed. Check authentication.'),
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-2">
        <Clock className="w-6 h-6 text-rose-500" />
        <h2 className="text-xl font-bold">Pending Feedback Governance</h2>
      </div>

      <TeamTabs />

      {isLoading ? (
        <div className="space-y-3">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-16 w-full" />)}</div>
      ) : !data || data.count === 0 ? (
        <EmptyState title="No Pending Feedback" description="All feedback is up to date for the selected team." />
      ) : (
        <div className="space-y-4">
          {/* Action bar */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button onClick={toggleSelectAll} className="flex items-center gap-2 text-sm font-medium hover:text-blue-600">
                {selected.size === practitioners.length ? <CheckSquare className="w-4 h-4" /> : <Square className="w-4 h-4" />}
                {selected.size === practitioners.length ? 'Deselect All' : 'Select All'}
              </button>
              <span className="text-sm text-[var(--text-secondary)]">
                {data.count} overdue items • {practitioners.length} practitioners
                {selected.size > 0 && ` • ${selected.size} selected`}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => previewMutation.mutate()}
                disabled={selected.size === 0 || previewMutation.isPending}
                className="btn-secondary flex items-center gap-2 text-sm disabled:opacity-50"
              >
                <Eye className="w-4 h-4" />
                Preview
              </button>
              <button
                onClick={() => sendMutation.mutate()}
                disabled={selected.size === 0 || sendMutation.isPending}
                className="btn-primary flex items-center gap-2 text-sm disabled:opacity-50"
              >
                <Send className="w-4 h-4" />
                {sendMutation.isPending ? 'Sending...' : `Send (${selected.size})`}
              </button>
              <button
                onClick={() => escalateMutation.mutate()}
                disabled={selected.size === 0 || escalateMutation.isPending}
                className="btn-danger flex items-center gap-2 text-sm disabled:opacity-50"
              >
                <ArrowUpCircle className="w-4 h-4" />
                {escalateMutation.isPending ? 'Escalating...' : 'Escalate'}
              </button>
            </div>
          </div>

          {/* Grouped list */}
          {practitioners.map((signum, idx) => {
            const items = grouped[signum]
            const first = items[0]
            const isExpanded = expanded.has(signum)
            const isSelected = selected.has(signum)

            return (
              <motion.div
                key={signum}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.02 }}
                className="glass-card overflow-hidden"
              >
                <div className="p-4 flex items-center justify-between cursor-pointer" onClick={() => toggleExpand(signum)}>
                  <div className="flex items-center gap-3">
                    <button onClick={(e) => { e.stopPropagation(); toggleSelect(signum) }} className="hover:text-blue-600">
                      {isSelected ? <CheckSquare className="w-5 h-5 text-blue-600" /> : <Square className="w-5 h-5" />}
                    </button>
                    <div className="w-9 h-9 rounded-full bg-rose-100 dark:bg-rose-900/30 flex items-center justify-center">
                      <Clock className="w-4 h-4 text-rose-600" />
                    </div>
                    <div>
                      <p className="font-medium text-sm">{first.name} <span className="text-xs text-[var(--text-secondary)]">({signum})</span></p>
                      <p className="text-xs text-[var(--text-secondary)]">{first.email} • {first.department}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-bold text-rose-500">{items.length} item{items.length > 1 ? 's' : ''}</span>
                    {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                  </div>
                </div>

                {isExpanded && (
                  <div className="border-t border-[var(--border)] px-4 pb-4">
                    <table className="w-full text-xs mt-3">
                      <thead>
                        <tr className="text-left text-[var(--text-secondary)]">
                          <th className="pb-2">Feedback ID</th>
                          <th className="pb-2">Asset Registry Id</th>
                          <th className="pb-2">Asset Name</th>
                          <th className="pb-2">Download Date</th>
                          <th className="pb-2">Due Date</th>
                          <th className="pb-2">Overdue</th>
                        </tr>
                      </thead>
                      <tbody>
                        {items.map((item) => (
                          <tr key={item.feedback_id} className="border-t border-[var(--border)]">
                            <td className="py-2">{item.feedback_id}</td>
                            <td className="py-2">{item.asset_registry_id}</td>
                            <td className="py-2">{item.asset_name}</td>
                            <td className="py-2">{item.download_date}</td>
                            <td className="py-2">{item.due_date}</td>
                            <td className="py-2 text-rose-500 font-medium">{item.overdue_duration}</td>
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
                    <p className="text-xs text-[var(--text-secondary)]">{p.item_count} feedback items</p>
                    <div className="text-xs border-t pt-2 mt-2" dangerouslySetInnerHTML={{ __html: p.body }} />
                  </div>
                ))}
                <div className="flex justify-end gap-2 pt-2">
                  <button onClick={() => setShowPreview(false)} className="btn-secondary text-sm">Cancel</button>
                  <button
                    onClick={() => sendMutation.mutate()}
                    disabled={sendMutation.isPending}
                    className="btn-primary flex items-center gap-2 text-sm"
                  >
                    <Mail className="w-4 h-4" />
                    {sendMutation.isPending ? 'Sending...' : 'Send All'}
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

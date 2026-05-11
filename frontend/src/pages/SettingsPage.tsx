import { useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import { Settings, Upload, CheckCircle, XCircle, Shield, Key, Trash2, Plus, Edit } from 'lucide-react'
import { uploadFile, getAuthStatus, setGraphToken } from '@/services/api'
import { useUploadStatus } from '@/hooks/useData'
import { useQueryClient, useQuery, useMutation } from '@tanstack/react-query'
import api from '@/services/api'

const FILE_TYPES = [
  { key: 'pat', label: 'PAT File', desc: 'PAT Details sheet with automation activities' },
  { key: 'mapping', label: 'Mapping File', desc: 'Export sheet with employee mapping data' },
  { key: 'savings', label: 'Savings File', desc: 'Savings - Line Manager sheet' },
  { key: 'download', label: 'Download File', desc: 'Asset download records with overdue info' },
]

export default function SettingsPage() {
  const { data: status, refetch } = useUploadStatus()
  const queryClient = useQueryClient()
  const [uploading, setUploading] = useState<string | null>(null)
  const [results, setResults] = useState<Record<string, { success: boolean; message: string }>>({})
  const [authStatus, setAuthStatus] = useState<boolean | null>(null)
  const [token, setToken] = useState('')
  const [tokenSaving, setTokenSaving] = useState(false)

  const handleUpload = useCallback(async (type: string, file: File) => {
    setUploading(type)
    try {
      const resp = await uploadFile(type, file)
      setResults(r => ({ ...r, [type]: { success: true, message: `Loaded ${resp.data.rows_loaded} rows` } }))
      refetch()
      queryClient.invalidateQueries()
    } catch (e: any) {
      const msg = e.response?.data?.detail || 'Upload failed'
      setResults(r => ({ ...r, [type]: { success: false, message: msg } }))
    }
    setUploading(null)
  }, [refetch, queryClient])

  const checkAuth = async () => {
    const res = await getAuthStatus()
    setAuthStatus(res.authenticated)
  }

  const handleSetToken = async () => {
    if (!token.trim()) return
    setTokenSaving(true)
    try {
      const res = await setGraphToken(token.trim())
      setAuthStatus(res.authenticated)
      alert('Token set successfully')
    } catch {
      alert('Failed to set token')
    }
    setTokenSaving(false)
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-3">
        <Settings className="w-6 h-6 text-primary-500" />
        <h2 className="text-xl font-bold">Settings & Data Management</h2>
      </div>

      {/* File Uploads */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {FILE_TYPES.map(({ key, label, desc }, idx) => (
          <motion.div
            key={key}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
            className="glass-card p-6"
          >
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="font-semibold">{label}</h3>
                <p className="text-xs text-[var(--text-secondary)]">{desc}</p>
              </div>
              {status && (
                <div className="flex items-center gap-1">
                  {(status as any)[key] ? (
                    <><CheckCircle className="w-4 h-4 text-green-500" /><span className="text-xs text-green-600">{(status as any)[`${key}_rows`]} rows</span></>
                  ) : (
                    <><XCircle className="w-4 h-4 text-slate-400" /><span className="text-xs text-slate-400">Not loaded</span></>
                  )}
                </div>
              )}
            </div>

            <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-slate-300 dark:border-slate-600 rounded-xl cursor-pointer hover:border-primary-400 transition-colors">
              <Upload className="w-8 h-8 text-slate-400 mb-2" />
              <span className="text-sm text-[var(--text-secondary)]">
                {uploading === key ? 'Uploading...' : 'Click to upload .xlsx / .xls'}
              </span>
              <input
                type="file"
                accept=".xlsx,.xls"
                className="hidden"
                onChange={(e) => {
                  const f = e.target.files?.[0]
                  if (f) handleUpload(key, f)
                }}
                disabled={uploading === key}
              />
            </label>

            {results[key] && (
              <p className={`text-xs mt-2 ${results[key].success ? 'text-green-600' : 'text-red-500'}`}>
                {results[key].message}
              </p>
            )}
          </motion.div>
        ))}
      </div>

      {/* Authentication */}
      <div className="glass-card p-6">
        <div className="flex items-center gap-3 mb-4">
          <Shield className="w-5 h-5 text-primary-500" />
          <h3 className="font-semibold">Microsoft Graph Authentication</h3>
        </div>
        <p className="text-xs text-[var(--text-secondary)] mb-4">
          Paste an access token from{' '}
          <a href="https://developer.microsoft.com/en-us/graph/graph-explorer" target="_blank" rel="noreferrer" className="text-primary-500 underline">
            Graph Explorer
          </a>
          {' '}(ensure Mail.Send permission is consented). Token expires in ~1 hour.
        </p>
        <div className="flex gap-3">
          <input
            type="password"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="Paste access token here..."
            className="flex-1 px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-[var(--bg-secondary)] text-sm"
          />
          <button onClick={handleSetToken} disabled={tokenSaving || !token.trim()} className="btn-primary flex items-center gap-2 text-sm disabled:opacity-50">
            <Key className="w-4 h-4" />
            {tokenSaving ? 'Saving...' : 'Set Token'}
          </button>
          <button onClick={checkAuth} className="btn-secondary text-sm">Check Status</button>
        </div>
        {authStatus !== null && (
          <p className={`text-sm mt-3 ${authStatus ? 'text-green-600' : 'text-amber-600'}`}>
            {authStatus ? '✓ Authenticated — ready to send mails' : '✗ Not authenticated'}
          </p>
        )}
      </div>

      {/* Exclusion List */}
      <ExclusionManager />

      {/* Savings Overrides */}
      <SavingsOverrideManager />
    </div>
  )
}

function SavingsOverrideManager() {
  const [feedbackId, setFeedbackId] = useState('')
  const [reuseSaving, setReuseSaving] = useState('')
  const [automationSaving, setAutomationSaving] = useState('')
  const queryClient = useQueryClient()

  const { data: overrides, refetch } = useQuery({
    queryKey: ['savings-overrides'],
    queryFn: () => api.get('/uploads/savings-overrides').then(r => r.data),
  })

  const setMutation = useMutation({
    mutationFn: (data: { feedback_id: string; reuse_saving: number; automation_saving: number }) =>
      api.post('/uploads/savings-overrides', data).then(r => r.data),
    onSuccess: () => {
      refetch()
      queryClient.invalidateQueries()
      setFeedbackId('')
      setReuseSaving('')
      setAutomationSaving('')
    },
  })

  const removeMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/uploads/savings-overrides/${id}`).then(r => r.data),
    onSuccess: () => { refetch(); queryClient.invalidateQueries() },
  })

  const handleAdd = () => {
    if (!feedbackId.trim()) return
    setMutation.mutate({
      feedback_id: feedbackId.trim(),
      reuse_saving: parseFloat(reuseSaving) || 0,
      automation_saving: parseFloat(automationSaving) || 0,
    })
  }

  return (
    <div className="glass-card p-6">
      <div className="flex items-center gap-3 mb-4">
        <Edit className="w-5 h-5 text-blue-500" />
        <h3 className="font-semibold">Savings Overrides</h3>
      </div>
      <p className="text-xs text-[var(--text-secondary)] mb-4">
        Update Reuse Saving and Automation Saving for specific Feedback IDs. These overrides persist across re-uploads.
      </p>

      <div className="flex gap-3 mb-4 flex-wrap">
        <input
          value={feedbackId}
          onChange={(e) => setFeedbackId(e.target.value)}
          placeholder="Feedback ID"
          className="px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-[var(--bg-secondary)] text-sm w-40"
        />
        <input
          value={reuseSaving}
          onChange={(e) => setReuseSaving(e.target.value)}
          placeholder="Reuse Saving"
          type="number"
          step="0.01"
          className="px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-[var(--bg-secondary)] text-sm w-36"
        />
        <input
          value={automationSaving}
          onChange={(e) => setAutomationSaving(e.target.value)}
          placeholder="Automation Saving"
          type="number"
          step="0.01"
          className="px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-[var(--bg-secondary)] text-sm w-36"
        />
        <button
          onClick={handleAdd}
          disabled={!feedbackId.trim() || setMutation.isPending}
          className="btn-primary flex items-center gap-2 text-sm disabled:opacity-50"
        >
          <Plus className="w-4 h-4" /> Set Override
        </button>
      </div>

      {overrides && overrides.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-[var(--text-secondary)] border-b border-[var(--border)]">
                <th className="pb-2 pr-4">Feedback ID</th>
                <th className="pb-2 pr-4 text-right">Reuse Saving</th>
                <th className="pb-2 pr-4 text-right">Automation Saving</th>
                <th className="pb-2 pr-4 text-right">Total</th>
                <th className="pb-2"></th>
              </tr>
            </thead>
            <tbody>
              {overrides.map((o: any) => (
                <tr key={o.feedback_id} className="border-b border-[var(--border)]">
                  <td className="py-2 pr-4">{o.feedback_id}</td>
                  <td className="py-2 pr-4 text-right">{o.reuse_saving}</td>
                  <td className="py-2 pr-4 text-right">{o.automation_saving}</td>
                  <td className="py-2 pr-4 text-right font-medium">{o.total_saving}</td>
                  <td className="py-2">
                    <button onClick={() => removeMutation.mutate(o.feedback_id)} className="text-red-500 hover:text-red-700">
                      <XCircle className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {(!overrides || overrides.length === 0) && <p className="text-xs text-[var(--text-secondary)]">No overrides set</p>}
    </div>
  )
}
  const [patId, setPatId] = useState('')
  const [feedbackId, setFeedbackId] = useState('')
  const queryClient = useQueryClient()

  const { data: exclusions, refetch } = useQuery({
    queryKey: ['exclusions'],
    queryFn: () => api.get('/uploads/exclusions').then(r => r.data),
  })

  const addPatMutation = useMutation({
    mutationFn: (ids: string[]) => api.post('/uploads/exclusions/pat', ids).then(r => r.data),
    onSuccess: () => { refetch(); queryClient.invalidateQueries(); setPatId('') },
  })

  const addFeedbackMutation = useMutation({
    mutationFn: (ids: string[]) => api.post('/uploads/exclusions/feedback', ids).then(r => r.data),
    onSuccess: () => { refetch(); queryClient.invalidateQueries(); setFeedbackId('') },
  })

  const removePatMutation = useMutation({
    mutationFn: (ids: string[]) => api.delete('/uploads/exclusions/pat', { data: ids }).then(r => r.data),
    onSuccess: () => { refetch(); queryClient.invalidateQueries() },
  })

  const removeFeedbackMutation = useMutation({
    mutationFn: (ids: string[]) => api.delete('/uploads/exclusions/feedback', { data: ids }).then(r => r.data),
    onSuccess: () => { refetch(); queryClient.invalidateQueries() },
  })

  return (
    <div className="glass-card p-6">
      <div className="flex items-center gap-3 mb-4">
        <Trash2 className="w-5 h-5 text-rose-500" />
        <h3 className="font-semibold">Permanent Exclusion List</h3>
      </div>
      <p className="text-xs text-[var(--text-secondary)] mb-4">
        Records added here will be excluded from all calculations, even after re-uploading data.
      </p>

      {/* Add PAT ID */}
      <div className="flex gap-3 mb-4">
        <input
          value={patId}
          onChange={(e) => setPatId(e.target.value)}
          placeholder="Enter PAT ID to exclude (comma-separated for multiple)"
          className="flex-1 px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-[var(--bg-secondary)] text-sm"
        />
        <button
          onClick={() => addPatMutation.mutate(patId.split(',').map(s => s.trim()).filter(Boolean))}
          disabled={!patId.trim()}
          className="btn-primary flex items-center gap-2 text-sm disabled:opacity-50"
        >
          <Plus className="w-4 h-4" /> Exclude PAT
        </button>
      </div>

      {/* Add Feedback ID */}
      <div className="flex gap-3 mb-6">
        <input
          value={feedbackId}
          onChange={(e) => setFeedbackId(e.target.value)}
          placeholder="Enter Feedback ID to exclude (comma-separated for multiple)"
          className="flex-1 px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-[var(--bg-secondary)] text-sm"
        />
        <button
          onClick={() => addFeedbackMutation.mutate(feedbackId.split(',').map(s => s.trim()).filter(Boolean))}
          disabled={!feedbackId.trim()}
          className="btn-primary flex items-center gap-2 text-sm disabled:opacity-50"
        >
          <Plus className="w-4 h-4" /> Exclude Feedback
        </button>
      </div>

      {/* Current Exclusions */}
      {exclusions && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="text-sm font-medium mb-2">Excluded PAT IDs ({exclusions.pat_ids?.length || 0})</h4>
            <div className="space-y-1 max-h-40 overflow-y-auto">
              {exclusions.pat_ids?.map((id: string) => (
                <div key={id} className="flex items-center justify-between text-xs bg-slate-50 dark:bg-slate-800 px-3 py-1.5 rounded">
                  <span>{id}</span>
                  <button onClick={() => removePatMutation.mutate([id])} className="text-red-500 hover:text-red-700">
                    <XCircle className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
              {(!exclusions.pat_ids || exclusions.pat_ids.length === 0) && <p className="text-xs text-[var(--text-secondary)]">None</p>}
            </div>
          </div>
          <div>
            <h4 className="text-sm font-medium mb-2">Excluded Feedback IDs ({exclusions.feedback_ids?.length || 0})</h4>
            <div className="space-y-1 max-h-40 overflow-y-auto">
              {exclusions.feedback_ids?.map((id: string) => (
                <div key={id} className="flex items-center justify-between text-xs bg-slate-50 dark:bg-slate-800 px-3 py-1.5 rounded">
                  <span>{id}</span>
                  <button onClick={() => removeFeedbackMutation.mutate([id])} className="text-red-500 hover:text-red-700">
                    <XCircle className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
              {(!exclusions.feedback_ids || exclusions.feedback_ids.length === 0) && <p className="text-xs text-[var(--text-secondary)]">None</p>}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function ExclusionManager() {
  const [patId, setPatId] = useState('')
  const [feedbackId, setFeedbackId] = useState('')
  const queryClient = useQueryClient()

  const { data: exclusions, refetch } = useQuery({
    queryKey: ['exclusions'],
    queryFn: () => api.get('/uploads/exclusions').then(r => r.data),
  })

  const addPatMutation = useMutation({
    mutationFn: (ids: string[]) => api.post('/uploads/exclusions/pat', ids).then(r => r.data),
    onSuccess: () => { refetch(); queryClient.invalidateQueries(); setPatId('') },
  })

  const addFeedbackMutation = useMutation({
    mutationFn: (ids: string[]) => api.post('/uploads/exclusions/feedback', ids).then(r => r.data),
    onSuccess: () => { refetch(); queryClient.invalidateQueries(); setFeedbackId('') },
  })

  const removePatMutation = useMutation({
    mutationFn: (ids: string[]) => api.delete('/uploads/exclusions/pat', { data: ids }).then(r => r.data),
    onSuccess: () => { refetch(); queryClient.invalidateQueries() },
  })

  const removeFeedbackMutation = useMutation({
    mutationFn: (ids: string[]) => api.delete('/uploads/exclusions/feedback', { data: ids }).then(r => r.data),
    onSuccess: () => { refetch(); queryClient.invalidateQueries() },
  })

  return (
    <div className="glass-card p-6">
      <div className="flex items-center gap-3 mb-4">
        <Trash2 className="w-5 h-5 text-rose-500" />
        <h3 className="font-semibold">Permanent Exclusion List</h3>
      </div>
      <p className="text-xs text-[var(--text-secondary)] mb-4">
        Records added here will be excluded from all calculations, even after re-uploading data.
      </p>

      {/* Add PAT ID */}
      <div className="flex gap-3 mb-4">
        <input
          value={patId}
          onChange={(e) => setPatId(e.target.value)}
          placeholder="Enter PAT ID to exclude (comma-separated for multiple)"
          className="flex-1 px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-[var(--bg-secondary)] text-sm"
        />
        <button
          onClick={() => addPatMutation.mutate(patId.split(',').map(s => s.trim()).filter(Boolean))}
          disabled={!patId.trim()}
          className="btn-primary flex items-center gap-2 text-sm disabled:opacity-50"
        >
          <Plus className="w-4 h-4" /> Exclude PAT
        </button>
      </div>

      {/* Add Feedback ID */}
      <div className="flex gap-3 mb-6">
        <input
          value={feedbackId}
          onChange={(e) => setFeedbackId(e.target.value)}
          placeholder="Enter Feedback ID to exclude (comma-separated for multiple)"
          className="flex-1 px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-[var(--bg-secondary)] text-sm"
        />
        <button
          onClick={() => addFeedbackMutation.mutate(feedbackId.split(',').map(s => s.trim()).filter(Boolean))}
          disabled={!feedbackId.trim()}
          className="btn-primary flex items-center gap-2 text-sm disabled:opacity-50"
        >
          <Plus className="w-4 h-4" /> Exclude Feedback
        </button>
      </div>

      {/* Current Exclusions */}
      {exclusions && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="text-sm font-medium mb-2">Excluded PAT IDs ({exclusions.pat_ids?.length || 0})</h4>
            <div className="space-y-1 max-h-40 overflow-y-auto">
              {exclusions.pat_ids?.map((id: string) => (
                <div key={id} className="flex items-center justify-between text-xs bg-slate-50 dark:bg-slate-800 px-3 py-1.5 rounded">
                  <span>{id}</span>
                  <button onClick={() => removePatMutation.mutate([id])} className="text-red-500 hover:text-red-700">
                    <XCircle className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
              {(!exclusions.pat_ids || exclusions.pat_ids.length === 0) && <p className="text-xs text-[var(--text-secondary)]">None</p>}
            </div>
          </div>
          <div>
            <h4 className="text-sm font-medium mb-2">Excluded Feedback IDs ({exclusions.feedback_ids?.length || 0})</h4>
            <div className="space-y-1 max-h-40 overflow-y-auto">
              {exclusions.feedback_ids?.map((id: string) => (
                <div key={id} className="flex items-center justify-between text-xs bg-slate-50 dark:bg-slate-800 px-3 py-1.5 rounded">
                  <span>{id}</span>
                  <button onClick={() => removeFeedbackMutation.mutate([id])} className="text-red-500 hover:text-red-700">
                    <XCircle className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
              {(!exclusions.feedback_ids || exclusions.feedback_ids.length === 0) && <p className="text-xs text-[var(--text-secondary)]">None</p>}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

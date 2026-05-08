import { useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import { Settings, Upload, CheckCircle, XCircle, Shield, Key } from 'lucide-react'
import { uploadFile, getAuthStatus, setGraphToken } from '@/services/api'
import { useUploadStatus } from '@/hooks/useData'
import { useQueryClient } from '@tanstack/react-query'

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
    </div>
  )
}

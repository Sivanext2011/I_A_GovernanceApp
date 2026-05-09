import { motion } from 'framer-motion'
import { Upload } from 'lucide-react'
import { useLeaderboard } from '@/hooks/useData'
import { Skeleton } from '@/components/ui'
import { formatNumber } from '@/lib/utils'
import { uploadPhoto } from '@/services/api'
import { useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'

interface LeaderEntry {
  signum: string
  name: string
  email: string
  department: string
  total_savings: number
  reuse_saving: number
  automation_saving: number
  photo_url: string
}

export function LeaderboardGrid() {
  const { data, isLoading } = useLeaderboard()

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-6">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="glass-card p-6 flex flex-col items-center">
            <Skeleton className="w-20 h-20 rounded-full mb-4" />
            <Skeleton className="h-4 w-24 mb-2" />
            <Skeleton className="h-6 w-20" />
          </div>
        ))}
      </div>
    )
  }

  if (!data || data.length === 0) {
    return <p className="text-center text-[var(--text-secondary)] py-8">No leaderboard data available</p>
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-6">
      {(data as LeaderEntry[]).map((entry, idx) => (
        <LeaderCard key={entry.signum} entry={entry} index={idx} />
      ))}
    </div>
  )
}

function LeaderCard({ entry, index }: { entry: LeaderEntry; index: number }) {
  const gradients = [
    'from-amber-400 to-orange-500',
    'from-slate-300 to-slate-400',
    'from-amber-600 to-amber-700',
    'from-primary-400 to-primary-600',
    'from-accent-400 to-accent-600',
  ]
  const fileRef = useRef<HTMLInputElement>(null)
  const queryClient = useQueryClient()

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    try {
      await uploadPhoto(entry.signum, file)
      queryClient.invalidateQueries({ queryKey: ['leaderboard'] })
    } catch {
      alert('Failed to upload photo')
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: index * 0.1, duration: 0.4 }}
      whileHover={{ scale: 1.05, boxShadow: '0 0 30px rgba(59,130,246,0.3)' }}
      className="glass-card p-6 flex flex-col items-center text-center cursor-pointer group"
    >
      {/* Photo */}
      <div className={`relative w-20 h-20 rounded-full bg-gradient-to-br ${gradients[index]} p-0.5 mb-4 group-hover:animate-glow`}>
        <img
          src={entry.photo_url}
          alt={entry.name}
          className="w-full h-full rounded-full object-cover bg-slate-200 dark:bg-slate-700"
          onError={(e) => {
            (e.target as HTMLImageElement).src = `https://ui-avatars.com/api/?name=${encodeURIComponent(entry.name)}&background=1e40af&color=fff&size=200`
          }}
        />
        <button
          onClick={(e) => { e.stopPropagation(); fileRef.current?.click() }}
          className="absolute -bottom-1 -right-1 w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center text-white hover:bg-blue-700 shadow"
          title="Upload photo"
        >
          <Upload className="w-3 h-3" />
        </button>
        <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={handleUpload} />
      </div>

      {/* Name */}
      <h4 className="font-semibold text-sm mb-1 line-clamp-1">{entry.name}</h4>
      <p className="text-xs text-[var(--text-secondary)] mb-3">{entry.department}</p>

      {/* Savings */}
      <div className={`px-3 py-1.5 rounded-full bg-gradient-to-r ${gradients[index]} text-white text-sm font-bold`}>
        {formatNumber(entry.total_savings)}
      </div>

      {/* Breakdown */}
      <div className="mt-3 text-xs text-[var(--text-secondary)] space-y-0.5">
        <p>Reuse: {formatNumber(entry.reuse_saving)}</p>
        <p>Automation: {formatNumber(entry.automation_saving)}</p>
      </div>
    </motion.div>
  )
}

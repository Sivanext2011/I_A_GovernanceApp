import { useState } from 'react'
import { Download, FileSpreadsheet, FileText, Image, Presentation } from 'lucide-react'
import { motion } from 'framer-motion'
import { useAppStore } from '@/store/useAppStore'
import { exportExcel, exportPDF, exportPNG, exportMonthlySavingsReport, exportAssetPresentation } from '@/services/api'
import { downloadBlob } from '@/lib/utils'
import { TeamTabs } from '@/components/ui'

const PPT_PERIODS = [
  { value: 'monthly', label: 'Monthly' },
  { value: 'quarterly', label: 'Quarterly' },
  { value: 'half-yearly', label: 'Half Yearly' },
  { value: 'year-end', label: 'Year End' },
]

export default function ExportsPage() {
  const { selectedTeam, selectedMonths } = useAppStore()
  const [loading, setLoading] = useState<string | null>(null)
  const [pptPeriod, setPptPeriod] = useState('monthly')
  const months = selectedMonths.length ? selectedMonths.join(',') : undefined

  const handleExport = async (type: string) => {
    setLoading(type)
    try {
      let resp
      if (type === 'excel') {
        resp = await exportExcel(selectedTeam, months)
        downloadBlob(resp.data, `report_${selectedTeam}.xlsx`)
      } else if (type === 'pdf') {
        resp = await exportPDF(selectedTeam, months)
        downloadBlob(resp.data, `report_${selectedTeam}.pdf`)
      } else if (type === 'png') {
        resp = await exportPNG(selectedTeam, 'trend', months)
        downloadBlob(resp.data, `chart_${selectedTeam}.png`)
      } else if (type === 'monthly-savings') {
        resp = await exportMonthlySavingsReport()
        downloadBlob(resp.data, 'Monthly_Savings_Report.xlsx')
      } else if (type === 'asset-ppt') {
        resp = await exportAssetPresentation(pptPeriod)
        downloadBlob(resp.data, `Asset_${pptPeriod.replace('-', '_')}.pptx`)
      }
    } catch (e) {
      alert('Export failed. Please ensure data is loaded.')
    }
    setLoading(null)
  }

  const exports = [
    { type: 'excel', icon: FileSpreadsheet, title: 'Excel Report', desc: 'Full KPI summary, leaderboard, and trend data', color: 'from-green-500 to-emerald-600' },
    { type: 'pdf', icon: FileText, title: 'PDF Report', desc: 'Executive-quality report with KPIs and charts', color: 'from-red-500 to-rose-600' },
    { type: 'png', icon: Image, title: 'Chart PNG', desc: 'High-resolution chart image export', color: 'from-blue-500 to-indigo-600' },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-2">
        <Download className="w-6 h-6 text-primary-500" />
        <h2 className="text-xl font-bold">Export Reports</h2>
      </div>

      <TeamTabs />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {exports.map(({ type, icon: Icon, title, desc, color }, idx) => (
          <motion.div
            key={type}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
            className="glass-card p-6 flex flex-col items-center text-center"
          >
            <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${color} flex items-center justify-center mb-4`}>
              <Icon className="w-8 h-8 text-white" />
            </div>
            <h3 className="font-semibold mb-1">{title}</h3>
            <p className="text-sm text-[var(--text-secondary)] mb-4">{desc}</p>
            <button
              onClick={() => handleExport(type)}
              disabled={loading === type}
              className="btn-primary w-full"
            >
              {loading === type ? 'Generating...' : `Export ${title}`}
            </button>
          </motion.div>
        ))}
      </div>

      <div className="flex items-center gap-3 mt-8 mb-2">
        <Download className="w-6 h-6 text-primary-500" />
        <h2 className="text-xl font-bold">Documents</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Monthly Savings Report */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-6 flex flex-col items-center text-center"
        >
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-teal-500 to-cyan-600 flex items-center justify-center mb-4">
            <FileSpreadsheet className="w-8 h-8 text-white" />
          </div>
          <h3 className="font-semibold mb-1">Monthly Savings Report</h3>
          <p className="text-sm text-[var(--text-secondary)] mb-4">Consolidated monthly savings data (Excel)</p>
          <button
            onClick={() => handleExport('monthly-savings')}
            disabled={loading === 'monthly-savings'}
            className="btn-primary w-full"
          >
            {loading === 'monthly-savings' ? 'Downloading...' : 'Download Report'}
          </button>
        </motion.div>

        {/* Asset Presentation with period selector */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-card p-6 flex flex-col items-center text-center"
        >
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-orange-500 to-amber-600 flex items-center justify-center mb-4">
            <Presentation className="w-8 h-8 text-white" />
          </div>
          <h3 className="font-semibold mb-1">Asset Presentation</h3>
          <p className="text-sm text-[var(--text-secondary)] mb-3">Asset analytics presentation (PowerPoint)</p>
          <select
            value={pptPeriod}
            onChange={(e) => setPptPeriod(e.target.value)}
            className="w-full mb-3 px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--bg-secondary)] text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            {PPT_PERIODS.map(({ value, label }) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
          <button
            onClick={() => handleExport('asset-ppt')}
            disabled={loading === 'asset-ppt'}
            className="btn-primary w-full"
          >
            {loading === 'asset-ppt' ? 'Downloading...' : 'Download Presentation'}
          </button>
        </motion.div>
      </div>
    </div>
  )
}

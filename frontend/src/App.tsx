import { Routes, Route } from 'react-router-dom'
import { useEffect } from 'react'
import MainLayout from '@/layouts/MainLayout'
import DashboardPage from '@/pages/DashboardPage'
import MissingSavingsPage from '@/pages/MissingSavingsPage'
import PendingFeedbackPage from '@/pages/PendingFeedbackPage'
import AnalyticsPage from '@/pages/AnalyticsPage'
import LeaderboardPage from '@/pages/LeaderboardPage'
import ExportsPage from '@/pages/ExportsPage'
import SettingsPage from '@/pages/SettingsPage'
import { useAppStore } from '@/store/useAppStore'

export default function App() {
  const { darkMode } = useAppStore()

  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode)
  }, [darkMode])

  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/missing-savings" element={<MissingSavingsPage />} />
        <Route path="/pending-feedback" element={<PendingFeedbackPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/leaderboard" element={<LeaderboardPage />} />
        <Route path="/exports" element={<ExportsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  )
}

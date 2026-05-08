import { Outlet, NavLink } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  LayoutDashboard, AlertTriangle, Clock, BarChart3, Trophy,
  Download, Settings, Moon, Sun, Menu, Activity
} from 'lucide-react'
import { useAppStore } from '@/store/useAppStore'
import { cn } from '@/lib/utils'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/missing-savings', icon: AlertTriangle, label: 'Missing Savings' },
  { to: '/pending-feedback', icon: Clock, label: 'Pending Feedback' },
  { to: '/analytics', icon: BarChart3, label: 'Monetization Analytics' },
  { to: '/leaderboard', icon: Trophy, label: 'Leaderboard' },
  { to: '/exports', icon: Download, label: 'Exports' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export default function MainLayout() {
  const { darkMode, toggleDarkMode, sidebarOpen, toggleSidebar } = useAppStore()

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <motion.aside
        initial={false}
        animate={{ width: sidebarOpen ? 280 : 0, opacity: sidebarOpen ? 1 : 0 }}
        className="h-full overflow-hidden border-r border-[var(--border)] bg-[var(--bg-secondary)] flex-shrink-0"
      >
        <div className="flex flex-col h-full w-[280px]">
          <div className="p-6 border-b border-[var(--border)]">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
                <Activity className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="font-bold text-sm leading-tight">Automation Savings</h1>
                <p className="text-xs text-[var(--text-secondary)]">Governance Platform</p>
              </div>
            </div>
          </div>

          <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
            {navItems.map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) => cn('nav-link', isActive && 'nav-link-active')}
              >
                <Icon className="w-5 h-5" />
                <span className="text-sm">{label}</span>
              </NavLink>
            ))}
          </nav>

          <div className="p-4 border-t border-[var(--border)]">
            <button onClick={toggleDarkMode} className="nav-link w-full">
              {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              <span className="text-sm">{darkMode ? 'Light Mode' : 'Dark Mode'}</span>
            </button>
          </div>
        </div>
      </motion.aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 border-b border-[var(--border)] bg-[var(--bg-secondary)] flex items-center px-6 gap-4">
          <button onClick={toggleSidebar} className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700">
            <Menu className="w-5 h-5" />
          </button>
          <h2 className="text-lg font-semibold">Automation Savings Governance & Monetization Analytics</h2>
        </header>
        <main className="flex-1 overflow-y-auto p-6 bg-[var(--bg-primary)]">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

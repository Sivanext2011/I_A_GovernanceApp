import { create } from 'zustand'

interface AppState {
  darkMode: boolean
  selectedTeam: string
  selectedMonths: string[]
  excludedMonths: string[]
  sidebarOpen: boolean
  toggleDarkMode: () => void
  setTeam: (team: string) => void
  setMonths: (months: string[]) => void
  setExcludedMonths: (months: string[]) => void
  toggleSidebar: () => void
}

export const useAppStore = create<AppState>((set) => ({
  darkMode: window.matchMedia('(prefers-color-scheme: dark)').matches,
  selectedTeam: 'Overall',
  selectedMonths: [],
  excludedMonths: [],
  sidebarOpen: true,
  toggleDarkMode: () => set((s) => {
    const next = !s.darkMode
    document.documentElement.classList.toggle('dark', next)
    return { darkMode: next }
  }),
  setTeam: (team) => set({ selectedTeam: team }),
  setMonths: (months) => set({ selectedMonths: months }),
  setExcludedMonths: (months) => set({ excludedMonths: months }),
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
}))

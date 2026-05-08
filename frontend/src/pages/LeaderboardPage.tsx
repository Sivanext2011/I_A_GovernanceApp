import { Trophy } from 'lucide-react'
import { TeamTabs, MonthMultiSelect } from '@/components/ui'
import { LeaderboardGrid } from '@/leaderboard/LeaderboardGrid'
import { useMonths } from '@/hooks/useData'

export default function LeaderboardPage() {
  const { data: monthsData } = useMonths()

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-2">
        <Trophy className="w-6 h-6 text-amber-500" />
        <h2 className="text-xl font-bold">Practitioner Leaderboard</h2>
      </div>

      <TeamTabs />
      {monthsData && <MonthMultiSelect months={monthsData.months} />}

      <LeaderboardGrid />
    </div>
  )
}

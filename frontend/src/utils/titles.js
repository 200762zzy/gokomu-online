export const TIERS = [
  { name: '初心者', icon: '🥚', tier: 1, minElo: 0, cssClass: 'tier-1' },
  { name: '青铜棋手', icon: '🥉', tier: 2, minElo: 1000, cssClass: 'tier-2' },
  { name: '白银棋手', icon: '🥈', tier: 3, minElo: 1200, cssClass: 'tier-3' },
  { name: '黄金棋手', icon: '🥇', tier: 4, minElo: 1400, cssClass: 'tier-4' },
  { name: '钻石棋手', icon: '💎', tier: 5, minElo: 1600, cssClass: 'tier-5' },
  { name: '大师', icon: '🔥', tier: 6, minElo: 1800, cssClass: 'tier-6' },
  { name: '棋圣', icon: '👑', tier: 7, minElo: 2000, cssClass: 'tier-7' },
]

export function getTitleInfo(elo) {
  for (let i = TIERS.length - 1; i >= 0; i--) {
    if (elo >= TIERS[i].minElo) return TIERS[i]
  }
  return TIERS[0]
}

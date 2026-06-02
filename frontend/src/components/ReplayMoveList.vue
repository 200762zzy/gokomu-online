<script setup>
import { computed } from 'vue'

const props = defineProps({
  moves: { type: Array, default: () => [] },
  currentStep: { type: Number, default: -1 },
  reviews: { type: Array, default: () => [] },
  reviewsLoading: { type: Boolean, default: false },
})

const emit = defineEmits(['goToStep'])

const BLACK = 1
const WHITE = 2

function getMoveLabel(move, prevAnalysis) {
  if (!move.analysis || !prevAnalysis) {
    return { text: '开局', color: '#aaa', desc: '', delta: null }
  }
  let delta
  let playerRate
  if (move.player === BLACK) {
    delta = move.analysis.black_win_rate - prevAnalysis.black_win_rate
    playerRate = move.analysis.black_win_rate
  } else {
    delta = move.analysis.white_win_rate - prevAnalysis.white_win_rate
    playerRate = move.analysis.white_win_rate
  }
  if (playerRate >= 0.95) return { text: '绝杀手', color: '#ff2d55', desc: '必胜之着', delta }
  if (playerRate >= 0.85) return { text: '决胜手', color: '#ff6b6b', desc: '胜势确立', delta }
  if (delta >= 0.20)      return { text: '妙手', color: '#ffd700', desc: '精妙着法', delta }
  if (delta >= 0.08)      return { text: '好手', color: '#4ecdc4', desc: '取得优势', delta }
  if (delta >= -0.08)     return { text: '正常', color: '#aaa', desc: '平稳进行', delta }
  if (delta >= -0.20)     return { text: '疑问手', color: '#e6a817', desc: '略有亏损', delta }
  return { text: '昏招', color: '#dc3545', desc: '严重失误', delta }
}

const reviewsMap = computed(() => {
  const map = {}
  for (const r of props.reviews) {
    map[r.step] = r
  }
  return map
})

const moveEntries = computed(() => {
  const entries = []
  let prevAnalysis = null
  for (let i = 0; i < props.moves.length; i++) {
    const move = props.moves[i]
    const apiReview = reviewsMap.value[i]
    let label
    if (apiReview) {
      label = { text: apiReview.label, delta: apiReview.delta }
      const colorMap = {
        '绝杀手': '#ff2d55', '决胜手': '#ff6b6b', '妙手': '#ffd700',
        '好手': '#4ecdc4', '正常': '#aaa', '疑问手': '#e6a817', '昏招': '#dc3545',
      }
      label.color = colorMap[apiReview.label] || '#aaa'
      label.desc = apiReview.detail || ''
    } else {
      label = getMoveLabel(move, prevAnalysis)
      if (props.reviews.length > 0 && !apiReview) {
        label.text = '—'
        label.color = '#555'
        label.desc = '暂无评价'
      }
    }
    const blackRate = move.analysis ? Math.round(move.analysis.black_win_rate * 100) : 50
    const whiteRate = move.analysis ? Math.round(move.analysis.white_win_rate * 100) : 50
    entries.push({
      index: i,
      move,
      label,
      blackRate,
      whiteRate,
      apiReview: apiReview || null,
    })
    prevAnalysis = move.analysis || prevAnalysis
  }
  return entries
})

const currentDetail = computed(() => {
  if (props.currentStep < 0 || props.currentStep >= props.moves.length) return null
  const entry = moveEntries.value[props.currentStep]
  if (!entry) return null
  return entry
})

function deltaStr(label) {
  if (label.delta === null || label.delta === undefined) return ''
  const pct = (label.delta * 100).toFixed(1)
  return (label.delta >= 0 ? '+' : '') + pct + '%'
}
</script>

<template>
  <div class="move-list-panel">
    <h3 class="panel-title">对局记录</h3>
    <div class="move-list-scroll">
      <div
        v-for="entry in moveEntries"
        :key="entry.index"
        :class="['move-row', { active: entry.index === currentStep }]"
        @click="emit('goToStep', entry.index)"
      >
        <span class="move-num">{{ entry.index + 1 }}</span>
        <span :class="['stone-icon', entry.move.player === BLACK ? 'black' : 'white']">
          {{ entry.move.player === BLACK ? '●' : '○' }}
        </span>
        <span class="move-coord">({{ entry.move.row }},{{ entry.move.col }})</span>

        <div class="rate-mini">
          <div class="rate-mini-bar">
            <div
              class="rate-mini-fill black-fill"
              :style="{ width: entry.blackRate + '%' }"
            ></div>
            <div
              class="rate-mini-fill white-fill"
              :style="{ width: entry.whiteRate + '%' }"
            ></div>
          </div>
        </div>

        <span
          v-if="entry.label.delta !== null && entry.label.delta !== undefined"
          :class="['delta', entry.label.delta >= 0 ? 'up' : 'down']"
        >
          {{ deltaStr(entry.label) }}
        </span>

        <span
          class="label-badge"
          :style="{
            background: entry.label.color,
            color: ['#ffd700','#e6a817','#aaa'].includes(entry.label.color) ? '#111' : '#fff',
          }"
        >
          {{ entry.label.text }}
        </span>
      </div>
    </div>

    <div v-if="reviewsLoading" class="detail-panel">
      <span class="detail-loading">评价加载中...</span>
    </div>

    <div v-else-if="currentDetail" class="detail-panel">
      <div class="detail-header">
        <span class="detail-num">第 {{ currentDetail.index + 1 }} 手</span>
        <span :class="['stone-icon', currentDetail.move.player === BLACK ? 'black' : 'white']">
          {{ currentDetail.move.player === BLACK ? '●' : '○' }}
        </span>
        <span class="detail-coord">({{ currentDetail.move.row }},{{ currentDetail.move.col }})</span>
        <span
          class="label-badge"
          :style="{
            background: currentDetail.label.color,
            color: ['#ffd700','#e6a817','#aaa'].includes(currentDetail.label.color) ? '#111' : '#fff',
          }"
        >{{ currentDetail.label.text }}</span>
        <span
          v-if="currentDetail.label.delta !== null && currentDetail.label.delta !== undefined"
          :class="['detail-delta', currentDetail.label.delta >= 0 ? 'up' : 'down']"
        >{{ deltaStr(currentDetail.label) }}</span>
      </div>
      <div class="detail-desc">{{ currentDetail.label.desc || '无详细评价' }}</div>
    </div>
  </div>
</template>

<style scoped>
.move-list-panel {
  background: rgba(22, 33, 62, 0.85);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  padding: 12px;
  width: 100%;
  max-height: 380px;
  display: flex;
  flex-direction: column;
}

.panel-title {
  font-size: 0.9rem;
  margin-bottom: 8px;
  color: #ccc;
}

.move-list-scroll {
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
  scrollbar-width: thin;
  scrollbar-color: #333 transparent;
}

.move-list-scroll::-webkit-scrollbar {
  width: 4px;
}

.move-list-scroll::-webkit-scrollbar-thumb {
  background: #444;
  border-radius: 2px;
}

.move-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.8rem;
  transition: background 0.15s;
}

.move-row:hover {
  background: #1a1a3e;
}

.move-row.active {
  background: #533483;
  outline: 1px solid #764ba2;
}

.move-num {
  color: #888;
  font-family: monospace;
  min-width: 22px;
  text-align: right;
}

.stone-icon {
  width: 14px;
  text-align: center;
  font-size: 0.8rem;
}

.stone-icon.black {
  color: #222;
  text-shadow: 0 0 2px rgba(255,255,255,0.2);
}

.stone-icon.white {
  color: #ddd;
  text-shadow: 0 0 2px rgba(0,0,0,0.3);
}

.move-coord {
  color: #aaa;
  font-family: monospace;
  min-width: 50px;
}

.rate-mini {
  flex: 1;
  min-width: 60px;
}

.rate-mini-bar {
  height: 8px;
  border-radius: 4px;
  display: flex;
  overflow: hidden;
  background: #0f3460;
}

.rate-mini-fill {
  height: 100%;
  transition: width 0.3s;
}

.rate-mini-fill.black-fill {
  background: #333;
}

.rate-mini-fill.white-fill {
  background: #ccc;
}

.delta {
  font-family: monospace;
  font-size: 0.75rem;
  min-width: 48px;
  text-align: right;
}

.delta.up, .detail-delta.up {
  color: #4ecdc4;
}

.delta.down, .detail-delta.down {
  color: #ff6b6b;
}

.label-badge {
  font-size: 0.65rem;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  white-space: nowrap;
  min-width: 32px;
  text-align: center;
}

.detail-panel {
  margin-top: 8px;
  padding: 10px;
  background: #0f3460;
  border-radius: 8px;
  flex-shrink: 0;
}

.detail-loading {
  color: #aaa;
  font-size: 0.85rem;
  text-align: center;
  display: block;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
  font-size: 0.85rem;
}

.detail-num {
  color: #888;
  font-family: monospace;
}

.detail-coord {
  color: #ccc;
  font-family: monospace;
}

.detail-delta {
  font-family: monospace;
  font-size: 0.8rem;
  font-weight: 700;
}

.detail-desc {
  font-size: 0.8rem;
  color: #bbb;
  line-height: 1.4;
}

</style>

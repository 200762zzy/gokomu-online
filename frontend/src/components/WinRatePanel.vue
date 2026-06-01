<script setup>
import { computed } from 'vue'

const props = defineProps({
  analysis: Object,
  loading: Boolean,
  moveLabel: Object,
})

const blackRate = computed(() => {
  if (!props.analysis) return 50
  return Math.round((props.analysis.black_win_rate || 0.5) * 100)
})

const whiteRate = computed(() => {
  if (!props.analysis) return 50
  return Math.round((props.analysis.white_win_rate || 0.5) * 100)
})
</script>

<template>
  <div class="winrate-panel">
    <h3 class="panel-title">
      AI 胜率分析
      <span v-if="loading" class="loading-spinner"></span>
    </h3>

    <div v-if="!analysis && !loading" class="no-data">
      <p>落子后将自动分析</p>
    </div>

      <div v-if="analysis" class="analysis-content">
        <div v-if="moveLabel" class="move-label-row" :style="{ background: moveLabel.color + '22', borderColor: moveLabel.color }">
          <span class="move-label-text" :style="{ color: moveLabel.color }">{{ moveLabel.text }}</span>
          <span class="move-label-desc">{{ moveLabel.desc }}</span>
          <span v-if="moveLabel.delta !== null" class="move-label-delta" :class="moveLabel.delta >= 0 ? 'up' : 'down'">
            {{ (moveLabel.delta >= 0 ? '+' : '') + (moveLabel.delta * 100).toFixed(1) + '%' }}
          </span>
        </div>
        <div class="rate-row">
          <div class="rate-bar-wrapper">
            <div class="rate-label">
              <span class="stone-dot black"></span> 黑棋
              <span class="rate-value">{{ blackRate }}%</span>
            </div>
            <div class="rate-bar-bg">
              <div
                class="rate-bar-fill black-fill"
                :style="{ width: blackRate + '%' }"
              ></div>
            </div>
          </div>
        </div>
        <div class="rate-row">
          <div class="rate-bar-wrapper">
            <div class="rate-label">
              <span class="stone-dot white"></span> 白棋
              <span class="rate-value">{{ whiteRate }}%</span>
            </div>
            <div class="rate-bar-bg">
              <div
                class="rate-bar-fill white-fill"
                :style="{ width: whiteRate + '%' }"
              ></div>
            </div>
          </div>
        </div>

      </div>
  </div>
</template>

<style scoped>
.winrate-panel {
  background: rgba(22, 33, 62, 0.85);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  padding: 16px;
  width: 100%;
}

.panel-title {
  font-size: 0.95rem;
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.loading-spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid #667eea;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.no-data {
  text-align: center;
  padding: 20px 0;
  color: #666;
  font-size: 0.85rem;
}

.analysis-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.rate-row {
  display: flex;
  align-items: center;
}

.rate-bar-wrapper {
  width: 100%;
}

.rate-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
  margin-bottom: 4px;
}

.stone-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.stone-dot.black {
  background: #222;
}

.stone-dot.white {
  background: #ddd;
  border: 1px solid #888;
}

.rate-value {
  margin-left: auto;
  font-weight: 700;
  font-family: monospace;
}

.rate-bar-bg {
  height: 12px;
  background: #0f3460;
  border-radius: 6px;
  overflow: hidden;
}

.rate-bar-fill {
  height: 100%;
  border-radius: 6px;
  transition: width 0.4s ease;
}

.black-fill {
  background: linear-gradient(90deg, #333, #111);
}

.white-fill {
  background: linear-gradient(90deg, #ccc, #eee);
}

.move-label-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid;
  font-size: 0.85rem;
}

.move-label-text {
  font-weight: 700;
  font-size: 0.95rem;
}

.move-label-desc {
  color: #aaa;
  font-size: 0.8rem;
  flex: 1;
}

.move-label-delta {
  font-family: monospace;
  font-weight: 700;
  font-size: 0.85rem;
}

.move-label-delta.up {
  color: #4ecdc4;
}

.move-label-delta.down {
  color: #ff6b6b;
}
</style>

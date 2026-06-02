<script setup>
import { computed } from 'vue'

const props = defineProps({
  blackTime: { type: Number, default: 1800000 },  // ms
  whiteTime: { type: Number, default: 1800000 },
  activeColor: { type: String, default: 'black' },
})

function formatTime(ms) {
  if (ms <= 0) return '超时'
  const totalSec = Math.ceil(ms / 1000)
  const min = Math.floor(totalSec / 60)
  const sec = totalSec % 60
  return `${min}:${sec.toString().padStart(2, '0')}`
}

function timePercent(ms) {
  const initial = 1800000 // 30 min
  return Math.max(0, Math.min(100, (ms / initial) * 100))
}

const blackPercent = computed(() => timePercent(props.blackTime))
const whitePercent = computed(() => timePercent(props.whiteTime))
</script>

<template>
  <div class="timer-display">
    <div class="timer-row" :class="{ active: activeColor === 'black', low: blackTime < 60000 }">
      <span class="timer-dot black"></span>
      <span class="timer-label">黑方</span>
      <div class="timer-bar-bg">
        <div class="timer-bar-fill black-fill" :style="{ width: blackPercent + '%' }"></div>
      </div>
      <span class="timer-value">{{ formatTime(blackTime) }}</span>
    </div>
    <div class="timer-row" :class="{ active: activeColor === 'white', low: whiteTime < 60000 }">
      <span class="timer-dot white"></span>
      <span class="timer-label">白方</span>
      <div class="timer-bar-bg">
        <div class="timer-bar-fill white-fill" :style="{ width: whitePercent + '%' }"></div>
      </div>
      <span class="timer-value">{{ formatTime(whiteTime) }}</span>
    </div>
  </div>
</template>

<style scoped>
.timer-display {
  background: rgba(22, 33, 62, 0.85);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.timer-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 6px;
  transition: background 0.2s;
}

.timer-row.active {
  background: rgba(102, 126, 234, 0.1);
}

.timer-row.low .timer-value {
  color: #dc3545;
  animation: blink 0.5s ease infinite alternate;
}

@keyframes blink {
  from { opacity: 1; }
  to { opacity: 0.5; }
}

.timer-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.timer-dot.black { background: #222; }
.timer-dot.white { background: #ddd; border: 1px solid #888; }

.timer-label {
  font-size: 0.8rem;
  color: #aaa;
  min-width: 28px;
}

.timer-bar-bg {
  flex: 1;
  height: 6px;
  background: #0f3460;
  border-radius: 3px;
  overflow: hidden;
}

.timer-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 1s linear;
}

.black-fill { background: #444; }
.white-fill { background: #ccc; }

.timer-value {
  font-family: monospace;
  font-size: 0.9rem;
  font-weight: 700;
  min-width: 44px;
  text-align: right;
  color: #ccc;
}

</style>

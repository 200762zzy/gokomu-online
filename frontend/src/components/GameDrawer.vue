<script setup>
import { ref, computed } from 'vue'
import GameInfo from './GameInfo.vue'
import WinRatePanel from './WinRatePanel.vue'
import ChatBox from './ChatBox.vue'

const props = defineProps({
  currentTurn: String,
  gameOver: Boolean,
  winner: String,
  gameResult: String,
  blackMoveCount: Number,
  whiteMoveCount: Number,
  analysis: Object,
  analyzing: Boolean,
  moveLabel: Object,
  roomId: String,
  waiting: Boolean,
})

const emit = defineEmits(['sendChat'])

const activeTab = ref(0)
const expanded = ref(false)

const tabs = [
  { label: '信息', icon: '📊' },
  { label: 'AI分析', icon: '🤖' },
  { label: '聊天', icon: '💬' },
]

function toggleExpand() {
  expanded.value = !expanded.value
}

function selectTab(index) {
  activeTab.value = index
  if (!expanded.value) {
    expanded.value = true
  }
}
</script>

<template>
  <div class="game-drawer" :class="{ expanded }">
    <div class="drawer-handle" @click="toggleExpand">
      <div class="handle-bar"></div>
    </div>

    <div class="drawer-tabs">
      <button
        v-for="(tab, i) in tabs"
        :key="i"
        class="drawer-tab"
        :class="{ active: activeTab === i }"
        @click="selectTab(i)"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        <span class="tab-label">{{ tab.label }}</span>
      </button>
    </div>

    <div class="drawer-content">
      <div v-show="activeTab === 0" class="drawer-panel">
        <GameInfo
          :current-turn="currentTurn"
          :game-over="gameOver"
          :winner="winner"
          :game-result="gameResult"
          :black-move-count="blackMoveCount"
          :white-move-count="whiteMoveCount"
        />
      </div>

      <div v-show="activeTab === 1" class="drawer-panel">
        <template v-if="!waiting">
          <WinRatePanel
            :analysis="analysis"
            :loading="analyzing"
            :move-label="moveLabel"
          />
        </template>
        <div v-else class="drawer-empty">等待对手加入...</div>
      </div>

      <div v-show="activeTab === 2" class="drawer-panel">
        <ChatBox :room-id="roomId" @send="(text) => emit('sendChat', text)" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.game-drawer {
  position: fixed;
  bottom: calc(56px + env(safe-area-inset-bottom, 0px));
  left: 0;
  right: 0;
  z-index: 50;
  background: rgba(15, 15, 40, 0.95);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px 16px 0 0;
  max-height: 50vh;
  transition: transform 0.3s ease;
  transform: translateY(calc(100% - 80px));
  display: flex;
  flex-direction: column;
}

.game-drawer.expanded {
  transform: translateY(0);
}

.drawer-handle {
  display: flex;
  justify-content: center;
  padding: 8px 0 4px;
  cursor: pointer;
  flex-shrink: 0;
}

.handle-bar {
  width: 36px;
  height: 4px;
  background: #555;
  border-radius: 2px;
}

.drawer-tabs {
  display: flex;
  gap: 4px;
  padding: 0 12px 8px;
  flex-shrink: 0;
}

.drawer-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px;
  background: none;
  border: none;
  color: #888;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  border-radius: 8px;
  min-height: 44px;
  transition: all 0.15s;
  -webkit-tap-highlight-color: transparent;
}

.drawer-tab:active {
  opacity: 0.7;
}

.drawer-tab.active {
  background: rgba(102, 126, 234, 0.15);
  color: #667eea;
}

.tab-icon {
  font-size: 1rem;
}

.drawer-content {
  flex: 1;
  overflow-y: auto;
  padding: 0 12px 12px;
}

.drawer-panel {
  min-height: 80px;
}

.drawer-empty {
  text-align: center;
  color: #888;
  padding: 32px 0;
  font-size: 0.9rem;
}
</style>

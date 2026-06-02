<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import TitleBadge from '../components/TitleBadge.vue'

const router = useRouter()
const authStore = useAuthStore()
const API_BASE = '/api'

const entries = ref([])
const loading = ref(true)
const page = ref(1)
const total = ref(0)
const limit = 50

async function fetchLeaderboard() {
  loading.value = true
  try {
    const resp = await fetch(`${API_BASE}/users/leaderboard?page=${page.value}&limit=${limit}`)
    if (resp.ok) {
      const data = await resp.json()
      entries.value = data.entries || []
      total.value = data.total || 0
    }
  } catch { /* ignore */ }
  loading.value = false
}

function goToProfile(userId) {
  router.push(`/profile/${userId}`)
}

function rankClass(rank) {
  if (rank === 1) return 'rank-gold'
  if (rank === 2) return 'rank-silver'
  if (rank === 3) return 'rank-bronze'
  return ''
}

onMounted(fetchLeaderboard)
</script>

<template>
  <div class="leaderboard-container">
    <h2 class="page-title">🏆 排行榜</h2>
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else class="list">
      <div
        v-for="entry in entries"
        :key="entry.id"
        class="entry-row"
        :class="{ 'is-me': entry.id === authStore.userId }"
        @click="goToProfile(entry.id)"
      >
        <span :class="['rank', rankClass(entry.rank)]">#{{ entry.rank }}</span>
        <span class="avatar-sm">{{ (entry.nickname || entry.username)[0] }}</span>
        <span class="name">{{ entry.nickname || entry.username }}</span>
        <TitleBadge v-if="entry.title" :title="entry.title" size="sm" />
        <span class="elo">{{ entry.elo }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.leaderboard-container {
  max-width: 600px;
  margin: 0 auto;
}

.page-title {
  font-size: 1.3rem;
  margin-bottom: 20px;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.entry-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(22, 33, 62, 0.85);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.15s;
}

.entry-row:hover { background: rgba(26, 26, 62, 0.9); }
.entry-row.is-me { border-color: #667eea; }

.rank {
  font-family: monospace;
  font-size: 1rem;
  font-weight: 700;
  min-width: 36px;
  color: #888;
}

.rank-gold { color: #ffd700; }
.rank-silver { color: #c0c0c0; }
.rank-bronze { color: #cd7f32; }

.avatar-sm {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #0f3460;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: #667eea;
}

.name { flex: 1; font-size: 0.95rem; }

.elo {
  font-family: monospace;
  font-weight: 700;
  color: #667eea;
  font-size: 1.05rem;
}

.loading { text-align: center; padding: 40px; color: #888; }

@media (max-width: 768px) {
  .entry-row { min-height: 48px; padding: 12px; }
  .page-title { font-size: 1.1rem; }
}
</style>

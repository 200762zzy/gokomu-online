<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '../stores/auth.js'

const authStore = useAuthStore()
function getHeaders() {
  const token = authStore.accessToken || localStorage.getItem('access_token') || ''
  return { 'Authorization': `Bearer ${token}` }
}

const tab = ref('users')
const users = ref([])
const rooms = ref([])
const logs = ref([])
const loading = ref(false)
const message = ref('')
const page = ref(1)
const totalUsers = ref(0)
const publicUrl = ref('')
const copied = ref(false)
const editingElo = ref(null)
const editEloVal = ref(0)
const logFilter = ref('')
const logTimer = ref(null)

async function fetchNgrokUrl() {
  try {
    const resp = await fetch('/api/ngrok-url')
    if (resp.ok) {
      const data = await resp.json()
      publicUrl.value = data.url || ''
    }
  } catch {}
}

function copyUrl() {
  if (!publicUrl.value) return
  navigator.clipboard.writeText(publicUrl.value)
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}

async function fetchUsers() {
  loading.value = true
  try {
    const resp = await fetch(`/api/admin/users?page=${page.value}&page_size=50`, { headers: getHeaders() })
    if (resp.ok) {
      const data = await resp.json()
      users.value = data.users
      totalUsers.value = data.total
    }
  } catch {}
  loading.value = false
}

async function fetchRooms() {
  loading.value = true
  try {
    const resp = await fetch('/api/admin/rooms', { headers: getHeaders() })
    if (resp.ok) {
      rooms.value = (await resp.json()).rooms
    }
  } catch {}
  loading.value = false
}

async function fetchLogs() {
  try {
    const params = new URLSearchParams({ lines: '200' })
    if (logFilter.value) params.set('level', logFilter.value)
    const resp = await fetch(`/api/admin/logs?${params}`, { headers: getHeaders() })
    if (resp.ok) {
      logs.value = (await resp.json()).logs
    }
  } catch {}
}

function startLogPolling() {
  fetchLogs()
  logTimer.value = setInterval(fetchLogs, 2000)
}

function stopLogPolling() {
  if (logTimer.value) {
    clearInterval(logTimer.value)
    logTimer.value = null
  }
}

async function setAdmin(userId, isAdmin) {
  if (!confirm(`确认${isAdmin ? '设置' : '取消'}该用户的管理员权限？`)) return
  try {
    const resp = await fetch('/api/admin/set-admin', {
      method: 'POST', headers: { ...getHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, is_admin: isAdmin }),
    })
    const data = await resp.json()
    message.value = data.message || '操作成功'
    fetchUsers()
  } catch { message.value = '操作失败' }
}

async function toggleBan(userId, isBanned) {
  if (!confirm(`确认${isBanned ? '封禁' : '解封'}该用户？`)) return
  try {
    const resp = await fetch('/api/admin/ban', {
      method: 'POST', headers: { ...getHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, is_banned: isBanned }),
    })
    const data = await resp.json()
    message.value = data.message || '操作成功'
    fetchUsers()
  } catch { message.value = '操作失败' }
}

async function deleteUser(userId) {
  if (!confirm('确认删除该用户及其所有数据？此操作不可恢复！')) return
  try {
    const resp = await fetch(`/api/admin/delete-user?user_id=${userId}`, {
      method: 'POST', headers: getHeaders(),
    })
    const data = await resp.json()
    message.value = data.message || '操作成功'
    fetchUsers()
  } catch { message.value = '操作失败' }
}

function startEditElo(user) {
  editingElo.value = user.id
  editEloVal.value = user.elo
}

async function saveElo(userId) {
  if (!confirm(`确认将 ELO 改为 ${editEloVal.value}？`)) return
  try {
    const resp = await fetch('/api/admin/set-elo', {
      method: 'POST', headers: { ...getHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, elo: editEloVal.value }),
    })
    const data = await resp.json()
    message.value = data.message || '操作成功'
    editingElo.value = null
    fetchUsers()
  } catch { message.value = '操作失败'; editingElo.value = null }
}

function cancelEditElo() {
  editingElo.value = null
}

async function closeRoom(roomId) {
  if (!confirm(`确认关闭房间 ${roomId}？`)) return
  try {
    const resp = await fetch('/api/admin/close-room', {
      method: 'POST', headers: { ...getHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ room_id: roomId }),
    })
    const data = await resp.json()
    message.value = data.message || '操作成功'
    fetchRooms()
  } catch { message.value = '操作失败' }
}

function levelColor(lvl) {
  const map = { INFO: '#888', WARNING: '#e6a817', ERROR: '#dc3545', CRITICAL: '#dc3545' }
  return map[lvl] || '#888'
}

function switchTab(t) {
  tab.value = t
  message.value = ''
  if (t === 'users') { stopLogPolling(); if (users.value.length === 0) fetchUsers() }
  if (t === 'rooms') { stopLogPolling(); if (rooms.value.length === 0) fetchRooms() }
  if (t === 'logs') { startLogPolling() }
}

onMounted(() => { fetchNgrokUrl(); fetchUsers() })
onUnmounted(stopLogPolling)
</script>

<template>
  <div class="admin-container">
    <h2 class="page-title">管理后台</h2>

    <div v-if="publicUrl" class="public-url-card">
      <span class="url-label">公网地址</span>
      <div class="url-row">
        <a :href="publicUrl" target="_blank" class="url-text">{{ publicUrl }}</a>
        <button class="btn-copy" @click="copyUrl">{{ copied ? '已复制' : '复制' }}</button>
      </div>
    </div>

    <div class="tab-bar">
      <button :class="['tab', { active: tab === 'users' }]" @click="switchTab('users')">用户管理</button>
      <button :class="['tab', { active: tab === 'rooms' }]" @click="switchTab('rooms')">房间管理</button>
      <button :class="['tab', { active: tab === 'logs' }]" @click="switchTab('logs')">系统日志</button>
    </div>

    <div v-if="message" class="toast">{{ message }}</div>

    <div v-if="tab === 'users'" class="section">
      <div class="section-header">用户列表 (共 {{ totalUsers }} 人)</div>
      <div v-if="loading" class="placeholder">加载中...</div>
      <div v-else-if="users.length === 0" class="placeholder">暂无用户</div>
      <div v-else v-for="u in users" :key="u.id" class="user-row">
        <div class="user-info">
          <span class="user-name">{{ u.nickname || u.username }}</span>
          <span class="user-sub">@{{ u.username }} · ELO
            <template v-if="editingElo === u.id">
              <input v-model.number="editEloVal" type="number" class="elo-input" min="0" max="9999" @keyup.enter="saveElo(u.id)" />
              <button class="btn-sm btn-elo-save" @click="saveElo(u.id)">保存</button>
              <button class="btn-sm btn-elo-cancel" @click="cancelEditElo">取消</button>
            </template>
            <template v-else>
              {{ u.elo }} <button class="btn-edit-elo" @click="startEditElo(u)">✏</button>
            </template>
          </span>
        </div>
        <div class="user-badges">
          <span v-if="u.is_banned" class="badge ban">封禁中</span>
          <span v-if="u.is_admin" class="badge admin">管理员</span>
        </div>
        <div class="user-actions">
          <button v-if="!u.is_admin" class="btn-sm btn-admin" @click="setAdmin(u.id, true)">设为管理</button>
          <button v-else class="btn-sm btn-outline" @click="setAdmin(u.id, false)">取消管理</button>
          <button :class="['btn-sm', u.is_banned ? 'btn-unban' : 'btn-ban']" @click="toggleBan(u.id, !u.is_banned)">
            {{ u.is_banned ? '解封' : '封禁' }}
          </button>
          <button class="btn-sm btn-danger" @click="deleteUser(u.id)">删除</button>
        </div>
      </div>
    </div>

    <div v-if="tab === 'rooms'" class="section">
      <div class="section-header">房间列表</div>
      <div v-if="loading" class="placeholder">加载中...</div>
      <div v-else-if="rooms.length === 0" class="placeholder">暂无活跃房间</div>
      <div v-else v-for="r in rooms" :key="r.room_id" class="room-row">
        <div class="room-info">
          <span class="room-id">#{{ r.room_id }}</span>
          <span class="room-players">{{ r.players.map(p => p.username).join(' vs ') || '等待中' }}</span>
          <span class="room-meta">{{ r.player_count }}人 · {{ r.spectator_count }}观战 · {{ r.is_gaming ? '对局中' : '等待中' }}</span>
        </div>
        <button class="btn-sm btn-danger" @click="closeRoom(r.room_id)">关闭</button>
      </div>
    </div>

    <div v-if="tab === 'logs'" class="section">
      <div class="section-header">
        <span>系统日志（每 2 秒自动刷新）</span>
        <select v-model="logFilter" class="log-filter" @change="fetchLogs">
          <option value="">全部级别</option>
          <option value="INFO">INFO</option>
          <option value="WARNING">WARNING</option>
          <option value="ERROR">ERROR</option>
          <option value="CRITICAL">CRITICAL</option>
        </select>
      </div>
      <div class="log-container">
        <div v-for="(l, i) in logs" :key="i" :class="['log-line', 'log-' + l.level.toLowerCase()]">
          <span class="log-time">{{ l.time.slice(11, 19) }}</span>
          <span class="log-level" :style="{ color: levelColor(l.level) }">{{ l.level.padEnd(8) }}</span>
          <span class="log-name">{{ l.name }}</span>
          <span class="log-msg">{{ l.message }}</span>
        </div>
        <div v-if="logs.length === 0" class="placeholder">暂无日志</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-container { max-width: 800px; margin: 0 auto; }
.page-title { font-size: 1.3rem; margin-bottom: 20px; }

.tab-bar { display: flex; gap: 4px; margin-bottom: 16px; background: #0f3460; border-radius: 10px; padding: 4px; }

.tab {
  flex: 1; padding: 10px; border: none; background: transparent; color: #aaa;
  border-radius: 8px; cursor: pointer; font-size: 0.9rem; font-weight: 600; transition: all 0.15s;
}
.tab.active { background: #667eea; color: #fff; }

.toast {
  background: #28a745; color: #fff; padding: 10px 16px;
  border-radius: 8px; margin-bottom: 16px; text-align: center;
}

.section {
  background: rgba(22, 33, 62, 0.85); backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 16px;
}

.section-header {
  font-size: 0.85rem; color: #888; margin-bottom: 12px; padding-bottom: 8px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.user-row, .room-row {
  display: flex; align-items: center; padding: 10px 0;
  border-bottom: 1px solid rgba(255,255,255,0.06); gap: 12px;
}
.user-row:last-child, .room-row:last-child { border-bottom: none; }

.user-info { flex: 1; display: flex; flex-direction: column; gap: 2px; }
.user-name { font-weight: 600; }
.user-sub { font-size: 0.8rem; color: #888; }

.user-badges { display: flex; gap: 4px; }
.badge {
  font-size: 0.7rem; padding: 2px 8px; border-radius: 10px; font-weight: 600;
}
.badge.ban { background: #dc3545; color: #fff; }
.badge.admin { background: #667eea; color: #fff; }

.user-actions { display: flex; gap: 4px; }

.btn-sm {
  padding: 4px 10px; border: none; border-radius: 6px; cursor: pointer;
  font-size: 0.8rem; font-weight: 600; transition: opacity 0.15s; white-space: nowrap;
}
.btn-sm:hover { opacity: 0.85; }
.btn-admin { background: #667eea; color: #fff; }
.btn-outline { background: transparent; border: 1px solid #667eea; color: #667eea; }
.btn-ban { background: #dc3545; color: #fff; }
.btn-unban { background: #28a745; color: #fff; }
.btn-danger { background: #c82333; color: #fff; }

.room-info { flex: 1; display: flex; flex-direction: column; gap: 2px; }
.room-id { font-family: monospace; font-weight: 700; color: #667eea; }
.room-players { font-size: 0.9rem; }
.room-meta { font-size: 0.8rem; color: #888; }

.placeholder { text-align: center; padding: 40px; color: #888; }

.public-url-card {
  background: linear-gradient(135deg, #1a1a4e, #16213e);
  border: 1px solid rgba(78, 205, 196, 0.3);
  border-radius: 12px; padding: 14px 18px; margin-bottom: 16px;
}

.url-label { font-size: 0.8rem; color: #4ecdc4; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }

.url-row { display: flex; align-items: center; gap: 12px; margin-top: 6px; }

.url-text {
  flex: 1; color: #4ecdc4; font-size: 0.95rem; font-family: monospace;
  text-decoration: none; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.url-text:hover { text-decoration: underline; }

.btn-copy {
  padding: 4px 14px; background: #4ecdc4; border: none; color: #0a0a1a;
  border-radius: 6px; cursor: pointer; font-size: 0.8rem; font-weight: 700; white-space: nowrap;
  transition: opacity 0.15s;
}
.btn-copy:hover { opacity: 0.85; }

/* ELO editing */
.elo-input {
  width: 70px; padding: 2px 6px; background: #0f3460; border: 1px solid #667eea;
  color: #eee; border-radius: 4px; font-size: 0.8rem; margin: 0 4px;
}
.btn-edit-elo {
  background: none; border: none; color: #667eea; cursor: pointer;
  font-size: 0.8rem; padding: 0 4px;
}
.btn-elo-save { background: #28a745; color: #fff; }
.btn-elo-cancel { background: #555; color: #fff; }

/* Log viewer */
.log-container {
  max-height: 500px; overflow-y: auto; font-family: 'Cascadia Code', 'Consolas', monospace;
  font-size: 0.78rem; line-height: 1.6; background: #0a0a1a; border-radius: 8px; padding: 12px;
}
.log-line { white-space: pre-wrap; word-break: break-all; }
.log-line + .log-line { margin-top: 2px; }
.log-time { color: #555; margin-right: 8px; }
.log-level { margin-right: 8px; font-weight: 600; }
.log-name { color: #667eea; margin-right: 12px; }
.log-msg { color: #ccc; }
.log-warning .log-msg { color: #e6a817; }
.log-error .log-msg { color: #dc3545; }
.log-critical .log-msg { color: #dc3545; font-weight: 700; }
.log-filter {
  background: #0f3460; color: #eee; border: 1px solid #333; border-radius: 4px;
  padding: 2px 8px; font-size: 0.8rem; cursor: pointer;
}
.section-header { display: flex; justify-content: space-between; align-items: center; }

@media (max-width: 768px) {
  .admin-tabs { overflow-x: auto; }
  .admin-card { padding: 12px; }
}
</style>

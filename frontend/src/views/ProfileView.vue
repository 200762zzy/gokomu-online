<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import TitleBadge from '../components/TitleBadge.vue'

const route = useRoute()
const authStore = useAuthStore()

const API_BASE = '/api'
const profile = ref(null)
const loading = ref(true)
const editing = ref(false)
const editNickname = ref('')
const saving = ref(false)
const customizing = ref(false)
const editBoardImage = ref('')
const editBackgroundImage = ref('')

const isOwnProfile = computed(() => {
  const userId = route.params.userId
  return !userId || parseInt(userId) === authStore.userId
})

async function fetchProfile() {
  loading.value = true
  const userId = route.params.userId
  const url = userId ? `${API_BASE}/users/${userId}` : `${API_BASE}/users/me`
  const headers = { 'Authorization': `Bearer ${authStore.accessToken}` }
  try {
    const resp = await fetch(url, { headers })
    if (resp.ok) {
      profile.value = await resp.json()
    }
  } catch { /* ignore */ }
  loading.value = false
}

function startEdit() {
  editNickname.value = profile.value?.nickname || ''
  editing.value = true
}

async function saveProfile() {
  saving.value = true
  try {
    const resp = await fetch(`${API_BASE}/users/me?nickname=${encodeURIComponent(editNickname.value)}`, {
      method: 'PUT',
      headers: { 'Authorization': `Bearer ${authStore.accessToken}` },
    })
    if (resp.ok) {
      profile.value = await resp.json()
      authStore.user.nickname = profile.value.nickname
    }
  } catch { /* ignore */ }
  saving.value = false
  editing.value = false
}

function startCustomize() {
  editBoardImage.value = profile.value?.board_image || ''
  editBackgroundImage.value = profile.value?.background_image || ''
  customizing.value = true
}

async function saveCustomize() {
  saving.value = true
  const params = new URLSearchParams()
  if (editBoardImage.value) params.set('board_image', editBoardImage.value)
  if (editBackgroundImage.value) params.set('background_image', editBackgroundImage.value)
  try {
    const resp = await fetch(`${API_BASE}/users/me?${params.toString()}`, {
      method: 'PUT',
      headers: { 'Authorization': `Bearer ${authStore.accessToken}` },
    })
    if (resp.ok) {
      profile.value = await resp.json()
      authStore.fetchProfile()
    }
  } catch { /* ignore */ }
  saving.value = false
  customizing.value = false
}

onMounted(fetchProfile)
</script>

<template>
  <div class="profile-container">
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="profile" class="profile-card">
      <div class="avatar-section">
        <div class="avatar">{{ (profile.nickname || profile.username)[0] }}</div>
        <div class="name-section">
          <h2>{{ profile.nickname || profile.username }}</h2>
          <span class="username">@{{ profile.username }}</span>
        </div>
      </div>

      <div class="stats-row">
        <div class="stat">
          <span class="stat-value">{{ profile.elo }}</span>
          <span class="stat-label">ELO 积分</span>
        </div>
        <div class="stat">
          <div class="stat-value-sm">
            <TitleBadge v-if="profile.title" :title="profile.title" size="lg" />
          </div>
          <span class="stat-label">称号</span>
        </div>
        <div class="stat">
          <span class="stat-value">{{ profile.is_admin ? '是' : '否' }}</span>
          <span class="stat-label">管理员</span>
        </div>
      </div>

      <div v-if="profile.created_at" class="info-row">
        <span class="info-label">注册时间</span>
        <span class="info-value">{{ profile.created_at }}</span>
      </div>

      <div v-if="isOwnProfile" class="actions">
        <button v-if="!editing" class="btn-edit" @click="startEdit">编辑资料</button>
        <button v-if="!customizing" class="btn-edit" @click="startCustomize">个性化</button>
      </div>

      <div v-if="editing" class="edit-form">
        <div class="form-group">
          <label>昵称</label>
          <input v-model="editNickname" class="input" maxlength="24" />
        </div>
        <div class="edit-actions">
          <button class="btn-save" :disabled="saving" @click="saveProfile">保存</button>
          <button class="btn-cancel" @click="editing = false">取消</button>
        </div>
      </div>

      <div v-if="customizing" class="edit-form">
        <div class="form-group">
          <label>棋盘背景图片 URL</label>
          <input v-model="editBoardImage" class="input" placeholder="https://example.com/board.png" />
        </div>
        <div class="form-group">
          <label>游戏背景图片 URL</label>
          <input v-model="editBackgroundImage" class="input" placeholder="https://example.com/background.png" />
        </div>
        <div class="edit-actions">
          <button class="btn-save" :disabled="saving" @click="saveCustomize">保存</button>
          <button class="btn-cancel" @click="customizing = false">取消</button>
        </div>
      </div>
    </div>
    <div v-else class="error">用户不存在</div>
  </div>
</template>

<style scoped>
.profile-container {
  max-width: 500px;
  margin: 0 auto;
}

.profile-card {
  background: rgba(22, 33, 62, 0.85);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 16px;
  padding: 28px;
}

.avatar-section {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.8rem;
  font-weight: 700;
  color: #fff;
}

.name-section h2 { font-size: 1.3rem; margin-bottom: 2px; }
.username { color: #888; font-size: 0.85rem; }

.stats-row {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.stat {
  flex: 1;
  background: #0f3460;
  border-radius: 10px;
  padding: 16px;
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 1.5rem;
  font-weight: 700;
  color: #667eea;
}

.stat-value-sm {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 2.2rem;
}

.stat-label {
  font-size: 0.8rem;
  color: #888;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-top: 1px solid rgba(255,255,255,0.06);
}

.info-label { color: #888; font-size: 0.85rem; }
.info-value { color: #aaa; font-size: 0.85rem; }

.actions { margin-top: 20px; }

.btn-edit {
  background: #0f3460;
  border: 1px solid #667eea;
  color: #667eea;
  padding: 8px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
  width: 100%;
}

.edit-form {
  margin-top: 16px;
  border-top: 1px solid rgba(255,255,255,0.06);
  padding-top: 16px;
}

.form-group { margin-bottom: 12px; }
.form-group label { display: block; font-size: 0.85rem; color: #aaa; margin-bottom: 4px; }

.input {
  width: 100%;
  padding: 10px 12px;
  background: #0f3460;
  border: 1px solid #333;
  color: #eee;
  border-radius: 8px;
  font-size: 1rem;
  outline: none;
}
.input:focus { border-color: #667eea; }

.edit-actions { display: flex; gap: 10px; }
.btn-save, .btn-cancel {
  padding: 8px 20px;
  border: none;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  color: #fff;
  flex: 1;
}
.btn-save { background: #28a745; }
.btn-cancel { background: #6c757d; }
.btn-save:disabled { opacity: 0.5; }

.loading, .error { text-align: center; padding: 40px; color: #888; }

@media (max-width: 768px) {
  .profile-container { max-width: 100%; }
  .profile-card { padding: 20px; }
  .stats-row { gap: 8px; }
  .stat { padding: 12px 8px; }
  .stat-value { font-size: 1.2rem; }
  .btn-edit { min-height: 44px; }
  .btn-save, .btn-cancel { min-height: 44px; }
  .input { font-size: 16px; }
}
</style>

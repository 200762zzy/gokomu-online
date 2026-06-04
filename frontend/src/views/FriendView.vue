<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useFriendStore } from '../stores/friend.js'
import { useGameStore } from '../stores/game.js'
import { getWsClient } from '../services/wsClient.js'
import TitleBadge from '../components/TitleBadge.vue'

const router = useRouter()
const friendStore = useFriendStore()
const gameStore = useGameStore()

const tab = ref('list')
const searchQuery = ref('')
const searchResults = ref([])
const searching = ref(false)
const sendMsg = ref('')
const invitation = ref(null)

const filteredFriends = computed(() => {
  const q = searchQuery.value.toLowerCase()
  if (!q) return friendStore.friends
  return friendStore.friends.filter(f =>
    (f.nickname || f.username).toLowerCase().includes(q) ||
    f.username.toLowerCase().includes(q)
  )
})

async function searchUsers() {
  const q = searchQuery.value.trim()
  if (!q) { searchResults.value = []; return }
  searching.value = true
  const token = localStorage.getItem('access_token')
  try {
    const resp = await fetch(`/api/friends/search?q=${encodeURIComponent(q)}`, {
      headers: { 'Authorization': `Bearer ${token}` },
    })
    if (resp.ok) {
      const data = await resp.json()
      searchResults.value = data.users || []
    }
  } catch {}
  searching.value = false
}

async function addFriend(username) {
  const err = await friendStore.sendRequest(username)
  sendMsg.value = err || '好友申请已发送'
  if (!err) searchResults.value = []
  setTimeout(() => { sendMsg.value = '' }, 3000)
}

async function acceptRequest(reqId) {
  await friendStore.respondRequest(reqId, true)
}

async function rejectRequest(reqId) {
  await friendStore.respondRequest(reqId, false)
}

async function removeFriend(friendId) {
  if (!confirm('确认删除好友？')) return
  await friendStore.removeFriend(friendId)
}

function goProfile(userId) {
  router.push(`/profile/${userId}`)
}

function switchTab(t) {
  tab.value = t
  if (t === 'requests') friendStore.fetchPendingRequests()
  if (t === 'list') friendStore.fetchFriends()
}

async function inviteToRoom(friendId) {
  let roomId = gameStore.currentRoomId
  if (!roomId) {
    try {
      const token = localStorage.getItem('access_token')
      const resp = await fetch('/api/my-active-room', {
        headers: { 'Authorization': `Bearer ${token}` },
      })
      if (resp.ok) {
        const data = await resp.json()
        if (data.game_type) roomId = data.room_id
      }
    } catch {}
  }
  if (!roomId) {
    sendMsg.value = '你当前不在房间中'
    setTimeout(() => { sendMsg.value = '' }, 3000)
    return
  }
  const ws = getWsClient()
  ws.send({ type: 'invite_to_room', to_user_id: friendId, room_id: roomId })
  sendMsg.value = '邀请已发送'
  setTimeout(() => { sendMsg.value = '' }, 2000)
}

function acceptInvitation() {
  const inv = invitation.value
  if (!inv) return
  invitation.value = null
  if (inv.game_in_progress) {
    router.push(`/spectate/${inv.room_id}`)
  } else {
    router.push(`/game/${inv.room_id}`)
  }
}

// Listen for friend online/offline via WS
const ws = getWsClient()
ws.on('friend_online', (msg) => {
  friendStore.setOnline(msg.user_id, true)
})
ws.on('friend_offline', (msg) => {
  friendStore.setOnline(msg.user_id, false)
})
ws.on('room_invitation', (msg) => {
  invitation.value = msg
})

onMounted(() => {
  friendStore.fetchFriends()
  friendStore.fetchPendingRequests()
})
</script>

<template>
  <div class="friend-container">
    <div class="card">
      <div class="card-header">
        <h2>好友</h2>
        <span v-if="friendStore.requestCount > 0" class="badge">{{ friendStore.requestCount }}</span>
      </div>

      <div class="tab-bar">
        <button :class="['tab', { active: tab === 'list' }]" @click="switchTab('list')">
          好友列表 ({{ friendStore.friends.length }})
        </button>
        <button :class="['tab', { active: tab === 'add' }]" @click="switchTab('add')">
          添加好友
        </button>
        <button :class="['tab', { active: tab === 'requests' }]" @click="switchTab('requests')">
          请求
          <span v-if="friendStore.requestCount > 0" class="badge-sm">{{ friendStore.requestCount }}</span>
        </button>
      </div>

      <div v-if="sendMsg" class="toast">{{ sendMsg }}</div>

      <!-- 好友列表 -->
      <div v-if="tab === 'list'" class="section">
        <div v-if="friendStore.friends.length === 0" class="empty">
          暂无好友，去"添加好友"页搜索添加吧
        </div>
        <div v-for="f in filteredFriends" :key="f.id" class="friend-row" @click="goProfile(f.id)">
          <span :class="['status-dot', { online: f.online }]" :title="f.online ? '在线' : '离线'"></span>
          <div class="friend-avatar">{{ (f.nickname || f.username)[0] }}</div>
          <div class="friend-info">
            <span class="friend-name">{{ f.nickname || f.username }}</span>
            <span class="friend-sub">
              @{{ f.username }} · {{ f.elo }}分
              <TitleBadge v-if="f.title" :title="f.title" size="sm" />
            </span>
          </div>
          <button
            class="btn-invite"
            :disabled="!f.online"
            :title="f.online ? '邀请加入房间' : '好友不在线'"
            @click.stop="inviteToRoom(f.id)"
          >邀请</button>
          <button class="btn-remove" @click.stop="removeFriend(f.id)">删除</button>
        </div>
      </div>

      <!-- 添加好友 -->
      <div v-if="tab === 'add'" class="section">
        <div class="search-box">
          <input v-model="searchQuery" type="text" placeholder="搜索用户名..." class="input"
            @input="searchUsers" @keyup.enter="searchUsers" />
        </div>
        <div v-if="searching" class="empty">搜索中...</div>
        <div v-else-if="searchResults.length === 0 && searchQuery" class="empty">无匹配用户</div>
        <div v-for="u in searchResults" :key="u.id" class="user-row">
          <div class="friend-avatar" @click="goProfile(u.id)">{{ (u.nickname || u.username)[0] }}</div>
          <div class="friend-info" @click="goProfile(u.id)">
            <span class="friend-name">{{ u.nickname || u.username }}</span>
            <span class="friend-sub">
              @{{ u.username }} · {{ u.elo }}分
              <TitleBadge v-if="u.title" :title="u.title" size="sm" />
            </span>
          </div>
          <button class="btn-add" @click="addFriend(u.username)">加好友</button>
        </div>
      </div>

      <!-- 好友请求 -->
      <div v-if="tab === 'requests'" class="section">
        <div v-if="friendStore.pendingRequests.length === 0" class="empty">暂无待处理请求</div>
        <div v-for="req in friendStore.pendingRequests" :key="req.request_id" class="request-row">
          <div class="friend-avatar">{{ (req.from_nickname || req.from_username)[0] }}</div>
          <div class="friend-info">
            <span class="friend-name">{{ req.from_nickname || req.from_username }}</span>
            <span class="friend-sub">@{{ req.from_username }} 请求添加你为好友</span>
          </div>
          <div class="request-actions">
            <button class="btn-accept" @click="acceptRequest(req.request_id)">接受</button>
            <button class="btn-reject" @click="rejectRequest(req.request_id)">拒绝</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 房间邀请弹窗 -->
    <Teleport to="body">
      <div v-if="invitation" class="overlay" @click.self="invitation = null">
        <div class="dialog">
          <h3>房间邀请</h3>
          <p>
            <strong>{{ invitation.from_username }}</strong> 邀请你加入房间
            <strong>#{{ invitation.room_id }}</strong>
          </p>
          <p class="dialog-desc">
            {{ invitation.black_name }}{{ invitation.white_name ? ' vs ' + invitation.white_name : ' 等待中' }}
            · {{ invitation.game_in_progress ? '对局中' : '等待中' }}
          </p>
          <div class="dialog-buttons">
            <button class="btn-reject" @click="invitation = null">拒绝</button>
            <button class="btn-accept" @click="acceptInvitation">接受</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.friend-container { max-width: 600px; margin: 0 auto; }

.card {
  background: rgba(22, 33, 62, 0.85); backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 20px;
}

.card-header { display: flex; align-items: center; gap: 8px; margin-bottom: 16px; }
.card-header h2 { font-size: 1.2rem; }

.badge {
  background: #dc3545; color: #fff; font-size: 0.75rem; padding: 2px 8px;
  border-radius: 10px; font-weight: 700;
}

.tab-bar { display: flex; gap: 4px; margin-bottom: 16px; background: #0f3460; border-radius: 10px; padding: 4px; }

.tab {
  flex: 1; padding: 8px; border: none; background: transparent; color: #aaa;
  border-radius: 8px; cursor: pointer; font-size: 0.85rem; font-weight: 600; transition: all 0.15s;
  display: flex; align-items: center; justify-content: center; gap: 4px;
}
.tab.active { background: #667eea; color: #fff; }

.badge-sm { background: #dc3545; color: #fff; font-size: 0.7rem; padding: 1px 6px; border-radius: 8px; font-weight: 700; }

.toast {
  background: #28a745; color: #fff; padding: 8px 12px; border-radius: 8px;
  margin-bottom: 12px; text-align: center; font-size: 0.85rem;
}

.section { min-height: 100px; }

.empty { text-align: center; padding: 40px 0; color: #888; font-size: 0.85rem; }

.friend-row, .user-row, .request-row {
  display: flex; align-items: center; gap: 10px; padding: 10px 0;
  border-bottom: 1px solid rgba(255,255,255,0.06); cursor: pointer;
}
.friend-row:last-child, .user-row:last-child, .request-row:last-child { border-bottom: none; }
.friend-row:hover, .user-row:hover, .request-row:hover { background: rgba(255,255,255,0.02); }

.status-dot {
  width: 8px; height: 8px; border-radius: 50%; background: #555; flex-shrink: 0;
}
.status-dot.online { background: #28a745; }

.friend-avatar {
  width: 36px; height: 36px; border-radius: 50%; background: #0f3460;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; color: #667eea; flex-shrink: 0;
}

.friend-info { flex: 1; display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.friend-name { font-weight: 600; font-size: 0.9rem; }
.friend-sub { font-size: 0.78rem; color: #888; display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }

.btn-invite {
  padding: 3px 10px; background: #4ecdc4; border: none; color: #fff; border-radius: 6px;
  cursor: pointer; font-size: 0.75rem; font-weight: 600;
}
.btn-invite:disabled { background: #444; color: #777; cursor: not-allowed; }
.btn-invite:hover:not(:disabled) { opacity: 0.85; }

.btn-remove { padding: 3px 10px; background: transparent; border: 1px solid #dc3545; color: #dc3545; border-radius: 6px; cursor: pointer; font-size: 0.75rem; font-weight: 600; }
.btn-remove:hover { background: #dc3545; color: #fff; }

.search-box { margin-bottom: 12px; }
.search-box .input { width: 100%; padding: 10px; background: #0f3460; border: 1px solid #333; color: #eee; border-radius: 8px; font-size: 0.9rem; outline: none; box-sizing: border-box; }
.search-box .input:focus { border-color: #667eea; }

.btn-add { padding: 4px 12px; background: #667eea; border: none; color: #fff; border-radius: 6px; cursor: pointer; font-size: 0.8rem; font-weight: 600; }

.request-actions { display: flex; gap: 4px; }
.btn-accept { padding: 4px 12px; background: #28a745; border: none; color: #fff; border-radius: 6px; cursor: pointer; font-size: 0.8rem; font-weight: 600; }
.btn-reject { padding: 4px 12px; background: #6c757d; border: none; color: #fff; border-radius: 6px; cursor: pointer; font-size: 0.8rem; font-weight: 600; }

.overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 100;
}
.dialog {
  background: #1a1a3e; border-radius: 12px; padding: 28px; text-align: center;
  box-shadow: 0 8px 30px rgba(0,0,0,0.5); max-width: 360px; width: 90%;
}
.dialog h3 { font-size: 1.1rem; margin-bottom: 16px; color: #eee; }
.dialog p { font-size: 0.95rem; margin-bottom: 8px; color: #ccc; }
.dialog-desc { font-size: 0.8rem; color: #888; margin-bottom: 20px; }
.dialog-buttons { display: flex; gap: 12px; justify-content: center; }
.dialog-buttons button { padding: 10px 28px; border: none; border-radius: 8px; font-size: 1rem; font-weight: 600; cursor: pointer; color: #fff; }

@media (max-width: 768px) {
  .friend-container { max-width: 100%; }
  .friend-row, .user-row, .request-row { min-height: 48px; }
  .tab { min-height: 44px; }
  .btn-invite, .btn-remove, .btn-add, .btn-accept, .btn-reject { min-height: 36px; }
}
</style>

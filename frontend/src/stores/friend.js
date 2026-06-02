import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useFriendStore = defineStore('friend', () => {
  const friends = ref([])
  const pendingRequests = ref([])
  const onlineStatus = ref({})
  const requestCount = ref(0)

  async function fetchFriends() {
    const token = localStorage.getItem('access_token')
    if (!token) return
    try {
      const resp = await fetch('/api/friends/', {
        headers: { 'Authorization': `Bearer ${token}` },
      })
      if (resp.ok) {
        const data = await resp.json()
        friends.value = (data.friends || []).map(f => ({
          ...f,
          online: !!onlineStatus.value[f.id],
        }))
      }
    } catch {}
  }

  async function fetchPendingRequests() {
    const token = localStorage.getItem('access_token')
    if (!token) return
    try {
      const resp = await fetch('/api/friends/pending', {
        headers: { 'Authorization': `Bearer ${token}` },
      })
      if (resp.ok) {
        const data = await resp.json()
        pendingRequests.value = data.requests || []
        requestCount.value = pendingRequests.value.length
      }
    } catch {}
  }

  async function sendRequest(username) {
    const token = localStorage.getItem('access_token')
    if (!token) return '请先登录'
    try {
      const resp = await fetch(`/api/friends/request?to_username=${encodeURIComponent(username)}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      })
      const data = await resp.json()
      if (resp.ok) return null
      return data.detail || '发送失败'
    } catch { return '网络错误' }
  }

  async function respondRequest(requestId, accept) {
    const token = localStorage.getItem('access_token')
    if (!token) return
    try {
      const resp = await fetch(`/api/friends/respond?request_id=${requestId}&accept=${accept}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      })
      if (resp.ok) {
        await fetchPendingRequests()
        await fetchFriends()
      }
    } catch {}
  }

  async function removeFriend(friendId) {
    const token = localStorage.getItem('access_token')
    if (!token) return
    try {
      await fetch(`/api/friends/${friendId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      })
      await fetchFriends()
    } catch {}
  }

  function setOnline(userId, status) {
    onlineStatus.value[userId] = status
    const f = friends.value.find(x => x.id === userId)
    if (f) f.online = status
  }

  function isOnline(userId) { return !!onlineStatus.value[userId] }

  return {
    friends, pendingRequests, onlineStatus, requestCount,
    fetchFriends, fetchPendingRequests, sendRequest, respondRequest,
    removeFriend, setOnline, isOnline,
  }
})

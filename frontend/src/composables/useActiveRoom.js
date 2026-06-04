import { ref, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '../stores/auth.js'

let pollTimer = null
const activeRoom = ref(null)

export function useActiveRoom() {
  const authStore = useAuthStore()

  async function fetchActiveRoom() {
    if (!authStore.isAuthenticated) {
      activeRoom.value = null
      return
    }
    try {
      const res = await fetch('/api/my-active-room', {
        headers: { Authorization: `Bearer ${authStore.accessToken}` },
      })
      if (res.ok) {
        const data = await res.json()
        activeRoom.value = data.game_type ? data : null
      }
    } catch { /* ignore */ }
  }

  onMounted(() => {
    fetchActiveRoom()
    if (!pollTimer) {
      pollTimer = setInterval(fetchActiveRoom, 5000)
    }
  })

  onUnmounted(() => {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  })

  return { activeRoom }
}

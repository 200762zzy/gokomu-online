import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getTitleInfo } from '../utils/titles.js'

const API_BASE = '/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const accessToken = ref(localStorage.getItem('access_token') || '')
  const refreshToken = ref(localStorage.getItem('refresh_token') || '')

  const isAuthenticated = computed(() => !!accessToken.value && !!user.value)
  const isAdmin = computed(() => user.value?.is_admin ?? false)
  const username = computed(() => user.value?.username ?? '')
  const userId = computed(() => user.value?.id ?? null)
  const elo = computed(() => user.value?.elo ?? 1000)
  const boardImage = computed(() => user.value?.board_image ?? '')
  const backgroundImage = computed(() => user.value?.background_image ?? '')
  const title = computed(() => getTitleInfo(user.value?.elo ?? 1000))

  async function login(username, password) {
    const resp = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })
    if (!resp.ok) {
      const err = await resp.json()
      throw new Error(err.detail || '登录失败')
    }
    const data = await resp.json()
    _setSession(data)
    await fetchProfile()
    return data
  }

  async function register(username, password, nickname) {
    const resp = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password, nickname }),
    })
    if (!resp.ok) {
      const err = await resp.json()
      throw new Error(err.detail || '注册失败')
    }
    const data = await resp.json()
    _setSession(data)
    await fetchProfile()
    return data
  }

  async function refresh() {
    if (!refreshToken.value) return false
    try {
      const resp = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken.value }),
      })
      if (!resp.ok) {
        logout()
        return false
      }
      const data = await resp.json()
      _setSession(data)
      await fetchProfile()
      return true
    } catch {
      logout()
      return false
    }
  }

  function _setSession(data) {
    accessToken.value = data.access_token
    refreshToken.value = data.refresh_token
    user.value = {
      id: data.user_id,
      username: data.username,
      nickname: data.nickname,
      elo: data.elo,
      is_admin: data.is_admin,
    }
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    localStorage.setItem('user', JSON.stringify(user.value))
  }

  function loadSession() {
    const stored = localStorage.getItem('user')
    if (stored && accessToken.value) {
      try {
        user.value = JSON.parse(stored)
      } catch {
        user.value = null
      }
    }
  }

  async function fetchProfile() {
    if (!accessToken.value) return
    try {
      const resp = await fetch(`${API_BASE}/users/me`, {
        headers: { 'Authorization': `Bearer ${accessToken.value}` },
      })
      if (resp.ok) {
        const data = await resp.json()
        user.value = { ...user.value, ...data }
        localStorage.setItem('user', JSON.stringify(user.value))
      }
    } catch { /* ignore */ }
  }

  function logout() {
    user.value = null
    accessToken.value = ''
    refreshToken.value = ''
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  }

  loadSession()
  if (accessToken.value) fetchProfile()

  return {
    user, accessToken, refreshToken,
    isAuthenticated, isAdmin, username, userId, elo,
    boardImage, backgroundImage, title,
    login, register, refresh, fetchProfile, logout, loadSession,
  }
})

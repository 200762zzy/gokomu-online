import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/HomeView.vue'),
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { guest: true },
  },
  {
    path: '/lobby',
    name: 'Lobby',
    component: () => import('../views/LobbyView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/game/:roomId',
    name: 'Game',
    component: () => import('../views/GameView.vue'),
    meta: { requiresAuth: true },
    props: true,
  },
  {
    path: '/spectate/:roomId',
    name: 'Spectate',
    component: () => import('../views/SpectateView.vue'),
    props: true,
  },
  {
    path: '/profile/:userId?',
    name: 'Profile',
    component: () => import('../views/ProfileView.vue'),
    props: true,
  },
  {
    path: '/leaderboard',
    name: 'Leaderboard',
    component: () => import('../views/LeaderboardView.vue'),
  },
  {
    path: '/friends',
    name: 'Friends',
    component: () => import('../views/FriendView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('../views/HistoryView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('../views/AdminView.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/local-game',
    name: 'LocalGame',
    component: () => import('../views/LocalGameView.vue'),
  },
  {
    path: '/ai-game',
    name: 'AiGame',
    component: () => import('../views/AiGameView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')
  const isAuthenticated = !!token

  if (to.meta.requiresAuth && !isAuthenticated) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (to.meta.guest && isAuthenticated) {
    next({ name: 'Home' })
  } else if (to.meta.requiresAdmin) {
    const raw = localStorage.getItem('user')
    let isAdmin = false
    if (raw) {
      try { isAdmin = JSON.parse(raw).is_admin } catch {}
    }
    if (!isAdmin) {
      next({ name: 'Home' })
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const isRegister = ref(false)
const username = ref('')
const password = ref('')
const nickname = ref('')
const error = ref('')
const loading = ref(false)

async function handleSubmit() {
  error.value = ''
  if (!username.value.trim() || !password.value.trim()) {
    error.value = '请填写用户名和密码'
    return
  }
  loading.value = true
  try {
    if (isRegister.value) {
      await authStore.register(username.value.trim(), password.value, nickname.value.trim())
    } else {
      await authStore.login(username.value.trim(), password.value)
    }
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

function toggleMode() {
  isRegister.value = !isRegister.value
  error.value = ''
}
</script>

<template>
  <div class="login-container">
    <div class="login-card">
      <h2>{{ isRegister ? '注册' : '登录' }}</h2>
      <p class="login-subtitle">五子棋在线对战平台</p>

      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label>用户名</label>
          <input v-model="username" type="text" placeholder="输入用户名" maxlength="24" class="input" />
        </div>
        <div class="form-group">
          <label>密码</label>
          <input v-model="password" type="password" placeholder="输入密码" class="input" />
        </div>
        <div v-if="isRegister" class="form-group">
          <label>昵称（可选）</label>
          <input v-model="nickname" type="text" placeholder="输入昵称" maxlength="32" class="input" />
        </div>

        <div v-if="error" class="error-msg">{{ error }}</div>

        <button type="submit" class="btn-submit" :disabled="loading">
          {{ loading ? '处理中...' : (isRegister ? '注册并登录' : '登录') }}
        </button>
      </form>

      <div class="toggle-mode">
        <span v-if="isRegister">已有账号？</span>
        <span v-else>没有账号？</span>
        <button class="btn-link" @click="toggleMode">
          {{ isRegister ? '去登录' : '去注册' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
}

.login-card {
  background: rgba(22, 33, 62, 0.85);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 16px;
  padding: 36px;
  width: 100%;
  max-width: 380px;
}

.login-card h2 {
  font-size: 1.5rem;
  text-align: center;
  margin-bottom: 4px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.login-subtitle {
  text-align: center;
  color: #888;
  font-size: 0.85rem;
  margin-bottom: 24px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 0.85rem;
  color: #aaa;
  margin-bottom: 6px;
}

.input {
  width: 100%;
  padding: 10px 12px;
  background: #0f3460;
  border: 1px solid #333;
  color: #eee;
  border-radius: 8px;
  font-size: 1rem;
  outline: none;
  transition: border-color 0.2s;
}

.input:focus {
  border-color: #667eea;
}

.error-msg {
  background: #dc3545;
  color: #fff;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 0.85rem;
  margin-bottom: 16px;
  text-align: center;
}

.btn-submit {
  width: 100%;
  padding: 12px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  color: #fff;
  font-size: 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: opacity 0.2s;
}

.btn-submit:hover:not(:disabled) { opacity: 0.9; }
.btn-submit:disabled { opacity: 0.5; cursor: not-allowed; }

.toggle-mode {
  text-align: center;
  margin-top: 20px;
  font-size: 0.85rem;
  color: #888;
}

.btn-link {
  background: none;
  border: none;
  color: #667eea;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 600;
  text-decoration: underline;
}

.btn-link:hover { color: #764ba2; }

@media (max-width: 768px) {
  .login-card { padding: 24px; }
  .login-card h2 { font-size: 1.3rem; }
  .btn-submit { min-height: 48px; }
  .input { font-size: 16px; }
}
</style>

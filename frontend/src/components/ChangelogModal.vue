<script setup>
import { changelog } from '../utils/changelog.js'

defineProps({
  show: Boolean,
})
const emit = defineEmits(['close'])
</script>

<template>
  <Teleport to="body">
    <div v-if="show" class="overlay" @click.self="emit('close')">
      <div class="modal">
        <div class="modal-header">
          <h3>📋 更新日志</h3>
          <button class="close-btn" @click="emit('close')">✕</button>
        </div>
        <div class="modal-body">
          <div v-for="entry in changelog" :key="entry.version" class="changelog-entry">
            <div class="changelog-version">
              <span class="version-badge">v{{ entry.version }}</span>
              <span class="version-date">{{ entry.date }}</span>
            </div>
            <ul class="changelog-items">
              <li v-for="(item, i) in entry.items" :key="i">{{ item }}</li>
            </ul>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-close" @click="emit('close')">关闭</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.overlay {
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal {
  background: #1a1a3e;
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5);
  max-width: 520px;
  width: 90%;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  animation: scaleIn 0.2s ease;
}

@keyframes scaleIn {
  from { transform: scale(0.95); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 12px;
}

.modal-header h3 {
  font-size: 1.1rem;
  color: #eee;
}

.close-btn {
  background: none;
  border: none;
  color: #888;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
}

.close-btn:hover {
  background: rgba(255,255,255,0.1);
  color: #eee;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 8px 24px 12px;
}

.changelog-entry {
  margin-bottom: 20px;
}

.changelog-entry:last-child {
  margin-bottom: 0;
}

.changelog-version {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.version-badge {
  display: inline-block;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  font-size: 0.8rem;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 10px;
}

.version-date {
  font-size: 0.8rem;
  color: #888;
}

.changelog-items {
  list-style: none;
}

.changelog-items li {
  position: relative;
  padding-left: 16px;
  margin-bottom: 6px;
  font-size: 0.85rem;
  color: #ccc;
  line-height: 1.5;
}

.changelog-items li::before {
  content: '•';
  position: absolute;
  left: 0;
  color: #667eea;
}

.modal-footer {
  padding: 12px 24px 20px;
  display: flex;
  justify-content: center;
}

.btn-close {
  padding: 8px 28px;
  border: none;
  border-radius: 6px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
}

.btn-close:hover {
  opacity: 0.9;
}
</style>

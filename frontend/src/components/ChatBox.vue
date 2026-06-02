<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useChatStore } from '../stores/chat.js'

const props = defineProps({
  roomId: String,
  global: { type: Boolean, default: false },
})

const chatStore = useChatStore()
const inputMessage = ref('')
const messagesContainer = ref(null)

const messages = computed(() => {
  if (props.global) {
    return chatStore.globalMessages
  }
  return chatStore.getRoomMessages(props.roomId || '')
})

const emit = defineEmits(['send'])

function sendMessage() {
  const text = inputMessage.value.trim()
  if (!text) return
  emit('send', text)
  inputMessage.value = ''
}

async function scrollToBottom() {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

onMounted(scrollToBottom)
</script>

<template>
  <div class="chatbox">
    <div class="chat-header">
      <span>{{ global ? '大厅聊天' : '房间聊天' }}</span>
    </div>
    <div ref="messagesContainer" class="chat-messages">
      <div v-if="messages.length === 0" class="chat-empty">
        暂无消息
      </div>
      <div v-for="(msg, i) in messages" :key="i" class="chat-msg">
        <span class="chat-from">{{ msg.from || msg.from_user }}：</span>
        <span class="chat-text">{{ msg.message }}</span>
      </div>
    </div>
    <div class="chat-input-row">
      <input
        v-model="inputMessage"
        type="text"
        placeholder="输入消息..."
        class="chat-input"
        maxlength="500"
        @keyup.enter="sendMessage"
      />
      <button class="chat-send" @click="sendMessage">发送</button>
    </div>
  </div>
</template>

<style scoped>
.chatbox {
  display: flex;
  flex-direction: column;
  background: rgba(22, 33, 62, 0.85);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px;
  overflow: hidden;
  height: 100%;
  min-height: 200px;
}

.chat-header {
  padding: 8px 12px;
  background: #0f3460;
  font-size: 0.8rem;
  font-weight: 600;
  color: #aaa;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 8px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 300px;
}

.chat-empty {
  text-align: center;
  color: #555;
  font-size: 0.8rem;
  padding: 16px 0;
}

.chat-msg {
  font-size: 0.82rem;
  line-height: 1.4;
  word-break: break-word;
}

.chat-from {
  color: #667eea;
  font-weight: 600;
}

.chat-text {
  color: #ccc;
}

.chat-input-row {
  display: flex;
  border-top: 1px solid rgba(255,255,255,0.06);
  padding: 6px;
  gap: 6px;
}

.chat-input {
  flex: 1;
  padding: 6px 10px;
  background: #0f3460;
  border: 1px solid #333;
  color: #eee;
  border-radius: 6px;
  font-size: 0.82rem;
  outline: none;
}

.chat-input:focus {
  border-color: #667eea;
}

.chat-send {
  padding: 6px 14px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  color: #fff;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 600;
}

.chat-send:hover {
  opacity: 0.9;
}

</style>

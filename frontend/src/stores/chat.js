import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useChatStore = defineStore('chat', () => {
  const globalMessages = ref([])
  const roomMessages = ref({})
  const maxMessages = 100

  function addGlobalMessage(msg) {
    globalMessages.value.push(msg)
    if (globalMessages.value.length > maxMessages) {
      globalMessages.value = globalMessages.value.slice(-maxMessages)
    }
  }

  function addRoomMessage(roomId, msg) {
    if (!roomMessages.value[roomId]) {
      roomMessages.value[roomId] = []
    }
    roomMessages.value[roomId].push(msg)
    if (roomMessages.value[roomId].length > maxMessages) {
      roomMessages.value[roomId] = roomMessages.value[roomId].slice(-maxMessages)
    }
  }

  function getRoomMessages(roomId) {
    return roomMessages.value[roomId] || []
  }

  return {
    globalMessages, roomMessages,
    addGlobalMessage, addRoomMessage, getRoomMessages,
  }
})

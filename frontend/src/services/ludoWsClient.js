let instance = null

class LudoWsClient {
  constructor() {
    this.ws = null
    this.listeners = {}
    this.reconnectTimer = null
    this._intentionalClose = false
    this.token = null
    this._authenticated = false
    this._reconnectAttempts = 0
    this._reconnectDelay = 3000
  }

  connect(token) {
    this.token = token
    this._intentionalClose = false
    this._authenticated = false
    this._reconnectAttempts = 0
    this._reconnectDelay = 3000
    this._createConnection()
  }

  _createConnection() {
    this._cleanup()
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/ludo`
    this.ws = new WebSocket(wsUrl)

    this.ws.onopen = () => {
      this._reconnectAttempts = 0
      this._reconnectDelay = 3000
      if (this.token) {
        this.send({ type: 'auth', token: this.token })
      }
    }

    this.ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data)
        if (msg.type === 'auth_ok') {
          this._authenticated = true
          this._emit('open', {})
          this._emit('auth_ok', msg)
        }
        this._emit(msg.type, msg)
      } catch { /* ignore */ }
    }

    this.ws.onclose = () => {
      this._emit('close', {})
      if (!this._intentionalClose) {
        this._scheduleReconnect()
      }
    }

    this.ws.onerror = () => {
      this._emit('error', {})
    }
  }

  _cleanup() {
    if (this.ws) {
      this.ws.onopen = null
      this.ws.onmessage = null
      this.ws.onerror = null
      this.ws.onclose = null
      this.ws.close()
      this.ws = null
    }
  }

  _scheduleReconnect() {
    if (this.reconnectTimer) return
    this._reconnectAttempts++
    if (this._reconnectAttempts > 5) return
    const delay = this._reconnectDelay
    this._reconnectDelay = Math.min(this._reconnectDelay * 1.5, 30000)
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null
      this._createConnection()
    }, delay)
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }

  on(event, callback) {
    if (!this.listeners[event]) this.listeners[event] = []
    this.listeners[event].push(callback)
    return () => this.off(event, callback)
  }

  off(event, callback) {
    const cbs = this.listeners[event]
    if (!cbs) return
    this.listeners[event] = cbs.filter(cb => cb !== callback)
  }

  _emit(event, data) {
    const cbs = this.listeners[event]
    if (!cbs) return
    for (const cb of [...cbs]) {
      try { cb(data) } catch (e) { console.error(e) }
    }
  }

  disconnect() {
    this._intentionalClose = true
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    this._cleanup()
  }

  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN
  }

  clearListeners() {
    this.listeners = {}
  }
}

export function getLudoWsClient() {
  if (!instance) {
    instance = new LudoWsClient()
  }
  return instance
}

const WS_BASE = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`

class WsClient {
  constructor() {
    this.ws = null
    this.listeners = {}
    this.reconnectTimer = null
    this._intentionalClose = false
    this.playerName = null
  }

  connect(playerName) {
    this.playerName = playerName
    this._intentionalClose = false
    this._createConnection()
  }

  _createConnection() {
    this._cleanup()

    this.ws = new WebSocket(WS_BASE)

    this.ws.onopen = () => {
      this._emit('open', {})
    }

    this.ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data)
        this._emit(msg.type, msg)
      } catch {}
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
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null
      this._createConnection()
    }, 3000)
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }

  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = []
    }
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
    this.listeners = {}
    this._cleanup()
  }
}

let instance = null
export function getWsClient() {
  if (!instance) {
    instance = new WsClient()
  }
  return instance
}

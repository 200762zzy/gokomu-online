let instance = null

class AudioManager {
  constructor() {
    if (instance) return instance
    this.ctx = null
    this.bgmBuffer = null
    this.bgmSource = null
    this.bgmGain = null
    this.sfxGain = null
    this._bgmPlaying = false
    this._bgmEnabled = true
    this._sfxEnabled = true
    this._gameType = 'gomoku'
    this._initialized = false
    this._pendingInit = null
    instance = this
  }

  async _ensureInit() {
    if (this._initialized) return
    if (this._pendingInit) return this._pendingInit
    this._pendingInit = this._init()
    return this._pendingInit
  }

  async _init() {
    try {
      this.ctx = new (window.AudioContext || window.webkitAudioContext)()
      this.bgmGain = this.ctx.createGain()
      this.bgmGain.gain.value = 0.3
      this.bgmGain.connect(this.ctx.destination)
      this.sfxGain = this.ctx.createGain()
      this.sfxGain.gain.value = 0.8
      this.sfxGain.connect(this.ctx.destination)
      this._initialized = true
    } catch (e) {
      this._pendingInit = null
    }
  }

  async _loadBGM(type) {
    const url = type === 'chess' ? '/audio/bgm-chess.mp3' : '/audio/bgm-gomoku.mp3'
    try {
      const resp = await fetch(url)
      const data = await resp.arrayBuffer()
      this.bgmBuffer = await this.ctx.decodeAudioData(data)
    } catch {
      try {
        const resp = await fetch('/audio/bgm.mp3')
        const data = await resp.arrayBuffer()
        this.bgmBuffer = await this.ctx.decodeAudioData(data)
      } catch {
        this.bgmBuffer = null
      }
    }
  }

  async _resumeCtx() {
    if (!this.ctx) return
    try {
      if (this.ctx.state === 'suspended') await this.ctx.resume()
    } catch {}
  }

  _scheduleBGM() {
    if (!this.ctx || !this.bgmBuffer || !this._bgmEnabled) return
    this.bgmSource = this.ctx.createBufferSource()
    this.bgmSource.buffer = this.bgmBuffer
    this.bgmSource.loop = true
    this.bgmSource.connect(this.bgmGain)
    this.bgmSource.start(0)
    this._bgmPlaying = true
  }

  set gameType(v) {
    this._gameType = v
    this.bgmBuffer = null
    if (this._initialized && this._bgmEnabled) {
      this.stopBGM()
      this.playBGM()
    }
  }

  get gameType() { return this._gameType }

  async playBGM() {
    await this._ensureInit()
    if (this._bgmPlaying) return
    if (!this.bgmBuffer) {
      await this._loadBGM(this._gameType)
    }
    if (!this.bgmBuffer) return
    this._bgmEnabled = true
    await this._resumeCtx()
    this._scheduleBGM()
  }

  stopBGM() {
    this._bgmPlaying = false
    if (this.bgmSource) {
      try { this.bgmSource.stop() } catch {}
      this.bgmSource = null
    }
  }

  setBGMVolume(v) {
    if (this.bgmGain) this.bgmGain.gain.value = Math.max(0, Math.min(1, v))
  }

  setSFXVolume(v) {
    if (this.sfxGain) this.sfxGain.gain.value = Math.max(0, Math.min(1, v))
  }

  get bgmEnabled() { return this._bgmEnabled }
  set bgmEnabled(v) {
    this._bgmEnabled = v
    if (!v) { this.stopBGM(); return }
    if (v) {
      if (!this.bgmBuffer) {
        this.__reloadAndPlay = true
      }
      this.playBGM()
    }
  }

  get sfxEnabled() { return this._sfxEnabled }
  set sfxEnabled(v) { this._sfxEnabled = v }

  // === Gomoku sounds ===

  async playGomokuStone() {
    await this._ensureInit()
    if (!this._sfxEnabled || !this.ctx) return
    await this._resumeCtx()
    const t = this.ctx.currentTime
    const out = this.sfxGain

    const osc1 = this.ctx.createOscillator()
    const g1 = this.ctx.createGain()
    osc1.type = 'sine'
    osc1.frequency.setValueAtTime(480, t)
    osc1.frequency.exponentialRampToValueAtTime(120, t + 0.08)
    g1.gain.setValueAtTime(0.6, t)
    g1.gain.exponentialRampToValueAtTime(0.001, t + 0.1)
    osc1.connect(g1); g1.connect(out)
    osc1.start(t); osc1.stop(t + 0.12)

    const osc2 = this.ctx.createOscillator()
    const g2 = this.ctx.createGain()
    osc2.type = 'triangle'
    osc2.frequency.setValueAtTime(2000, t)
    osc2.frequency.exponentialRampToValueAtTime(600, t + 0.04)
    g2.gain.setValueAtTime(0.35, t)
    g2.gain.exponentialRampToValueAtTime(0.001, t + 0.05)
    osc2.connect(g2); g2.connect(out)
    osc2.start(t); osc2.stop(t + 0.06)
  }

  // === Chinese Chess sounds ===

  async playChessMove() {
    await this._ensureInit()
    if (!this._sfxEnabled || !this.ctx) return
    await this._resumeCtx()
    const t = this.ctx.currentTime
    const out = this.sfxGain

    const osc = this.ctx.createOscillator()
    const g = this.ctx.createGain()
    osc.type = 'triangle'
    osc.frequency.setValueAtTime(280, t)
    osc.frequency.exponentialRampToValueAtTime(100, t + 0.15)
    g.gain.setValueAtTime(0.6, t)
    g.gain.exponentialRampToValueAtTime(0.001, t + 0.2)
    osc.connect(g); g.connect(out)
    osc.start(t); osc.stop(t + 0.25)
  }

  async playChessCapture() {
    await this._ensureInit()
    if (!this._sfxEnabled || !this.ctx) return
    await this._resumeCtx()
    const t = this.ctx.currentTime
    const out = this.sfxGain

    const osc = this.ctx.createOscillator()
    const g = this.ctx.createGain()
    osc.type = 'sawtooth'
    osc.frequency.setValueAtTime(200, t)
    osc.frequency.exponentialRampToValueAtTime(60, t + 0.2)
    g.gain.setValueAtTime(0.7, t)
    g.gain.exponentialRampToValueAtTime(0.001, t + 0.25)
    osc.connect(g); g.connect(out)
    osc.start(t); osc.stop(t + 0.3)

    const noise = this.ctx.createOscillator()
    const gn = this.ctx.createGain()
    noise.type = 'square'
    noise.frequency.setValueAtTime(800, t)
    noise.frequency.exponentialRampToValueAtTime(200, t + 0.1)
    gn.gain.setValueAtTime(0.35, t)
    gn.gain.exponentialRampToValueAtTime(0.001, t + 0.12)
    noise.connect(gn); gn.connect(out)
    noise.start(t); noise.stop(t + 0.15)
  }

  async playChessCheck() {
    await this._ensureInit()
    if (!this._sfxEnabled || !this.ctx) return
    await this._resumeCtx()
    const t = this.ctx.currentTime
    const out = this.sfxGain

    const osc1 = this.ctx.createOscillator()
    const g1 = this.ctx.createGain()
    osc1.type = 'square'
    osc1.frequency.setValueAtTime(880, t)
    osc1.frequency.setValueAtTime(660, t + 0.15)
    osc1.frequency.setValueAtTime(880, t + 0.3)
    osc1.frequency.setValueAtTime(660, t + 0.45)
    g1.gain.setValueAtTime(0.25, t)
    g1.gain.linearRampToValueAtTime(0.3, t + 0.1)
    g1.gain.exponentialRampToValueAtTime(0.001, t + 0.6)
    osc1.connect(g1); g1.connect(out)
    osc1.start(t); osc1.stop(t + 0.6)

    const osc2 = this.ctx.createOscillator()
    const g2 = this.ctx.createGain()
    osc2.type = 'sine'
    osc2.frequency.setValueAtTime(1320, t)
    osc2.frequency.setValueAtTime(990, t + 0.15)
    osc2.frequency.setValueAtTime(1320, t + 0.3)
    osc2.frequency.setValueAtTime(990, t + 0.45)
    g2.gain.setValueAtTime(0.25, t)
    g2.gain.exponentialRampToValueAtTime(0.001, t + 0.5)
    osc2.connect(g2); g2.connect(out)
    osc2.start(t); osc2.stop(t + 0.5)
  }

  async playChessEat() {
    await this._ensureInit()
    if (!this._sfxEnabled || !this.ctx) return
    await this._resumeCtx()
    const t = this.ctx.currentTime
    const out = this.sfxGain

    const osc = this.ctx.createOscillator()
    const g = this.ctx.createGain()
    osc.type = 'square'
    osc.frequency.setValueAtTime(1200, t)
    osc.frequency.exponentialRampToValueAtTime(400, t + 0.08)
    g.gain.setValueAtTime(0.5, t)
    g.gain.exponentialRampToValueAtTime(0.001, t + 0.1)
    osc.connect(g); g.connect(out)
    osc.start(t); osc.stop(t + 0.12)
  }

  // === Legacy (aliases / kept for compatibility) ===

  async playStone() { return this.playGomokuStone() }

  async playClick() {
    await this._ensureInit()
    if (!this._sfxEnabled || !this.ctx) return
    await this._resumeCtx()
    const t = this.ctx.currentTime
    const osc1 = this.ctx.createOscillator()
    const osc2 = this.ctx.createOscillator()
    const gain = this.ctx.createGain()
    osc1.type = 'sine'
    osc1.frequency.value = 1500
    osc2.type = 'sine'
    osc2.frequency.value = 3800
    gain.gain.setValueAtTime(0.4, t)
    gain.gain.exponentialRampToValueAtTime(0.001, t + 0.03)
    osc1.connect(gain)
    osc2.connect(gain)
    gain.connect(this.sfxGain)
    osc1.start(t)
    osc1.stop(t + 0.04)
    osc2.start(t)
    osc2.stop(t + 0.04)
  }

  async playWin() {
    await this._ensureInit()
    if (!this._sfxEnabled || !this.ctx) return
    await this._resumeCtx()
    const notes = [523, 659, 784]
    notes.forEach((freq, i) => {
      const osc = this.ctx.createOscillator()
      const gain = this.ctx.createGain()
      osc.type = 'sine'
      osc.frequency.value = freq
      const t = this.ctx.currentTime + i * 0.15
      gain.gain.setValueAtTime(0.5, t)
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.3)
      osc.connect(gain)
      gain.connect(this.sfxGain)
      osc.start(t)
      osc.stop(t + 0.35)
    })
  }

  async playLose() {
    await this._ensureInit()
    if (!this._sfxEnabled || !this.ctx) return
    await this._resumeCtx()
    const notes = [400, 350, 300]
    notes.forEach((freq, i) => {
      const osc = this.ctx.createOscillator()
      const gain = this.ctx.createGain()
      osc.type = 'sawtooth'
      osc.frequency.value = freq
      const t = this.ctx.currentTime + i * 0.2
      gain.gain.setValueAtTime(0.35, t)
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.3)
      osc.connect(gain)
      gain.connect(this.sfxGain)
      osc.start(t)
      osc.stop(t + 0.35)
    })
  }

  async playTitleSound(tier) {
    await this._ensureInit()
    if (!this._sfxEnabled || !this.ctx) return
    await this._resumeCtx()
    const t = this.ctx.currentTime
    const ctx = this.ctx
    const out = this.sfxGain

    if (tier <= 1) {
      const osc = ctx.createOscillator()
      const g = ctx.createGain()
      osc.type = 'sine'
      osc.frequency.value = 440
      g.gain.setValueAtTime(0.25, t)
      g.gain.exponentialRampToValueAtTime(0.001, t + 0.12)
      osc.connect(g); g.connect(out)
      osc.start(t); osc.stop(t + 0.15)
    } else if (tier === 2) {
      const osc = ctx.createOscillator()
      const g = ctx.createGain()
      osc.type = 'sine'
      osc.frequency.value = 880
      g.gain.setValueAtTime(0.3, t)
      g.gain.exponentialRampToValueAtTime(0.001, t + 0.3)
      osc.connect(g); g.connect(out)
      osc.start(t); osc.stop(t + 0.35)
    } else if (tier === 3) {
      ;[1200, 1500, 1800].forEach((f, i) => {
        const osc = ctx.createOscillator()
        const g = ctx.createGain()
        osc.type = 'sine'
        osc.frequency.value = f
        const tt = t + i * 0.08
        g.gain.setValueAtTime(0.15, tt)
        g.gain.exponentialRampToValueAtTime(0.001, tt + 0.3)
        osc.connect(g); g.connect(out)
        osc.start(tt); osc.stop(tt + 0.35)
      })
    } else if (tier === 4) {
      ;[523, 659, 784, 1047].forEach((f, i) => {
        const osc = ctx.createOscillator()
        const g = ctx.createGain()
        osc.type = 'sine'
        osc.frequency.value = f
        const tt = t + i * 0.12
        g.gain.setValueAtTime(0.2, tt)
        g.gain.linearRampToValueAtTime(0.25, tt + 0.1)
        g.gain.exponentialRampToValueAtTime(0.001, tt + 0.5)
        osc.connect(g); g.connect(out)
        osc.start(tt); osc.stop(tt + 0.55)
      })
    } else if (tier === 5) {
      ;[587, 659, 784, 880].forEach((f, i) => {
        const osc = ctx.createOscillator()
        const g = ctx.createGain()
        osc.type = 'sine'
        osc.frequency.value = f
        const tt = t + i * 0.12
        g.gain.setValueAtTime(0.2, tt)
        g.gain.exponentialRampToValueAtTime(0.001, tt + 0.4)
        osc.connect(g); g.connect(out)
        osc.start(tt); osc.stop(tt + 0.45)
      })
    } else if (tier === 6) {
      ;[1047, 1175, 1319, 1397, 1568].forEach((f, i) => {
        const osc = ctx.createOscillator()
        const g = ctx.createGain()
        osc.type = 'sine'
        osc.frequency.value = f
        const tt = t + i * 0.1
        g.gain.setValueAtTime(0.15, tt)
        g.gain.exponentialRampToValueAtTime(0.001, tt + 0.3)
        osc.connect(g); g.connect(out)
        osc.start(tt); osc.stop(tt + 0.35)
      })
    } else if (tier === 7) {
      const osc = ctx.createOscillator()
      const noise = ctx.createOscillator()
      const g1 = ctx.createGain()
      const g2 = ctx.createGain()
      osc.type = 'sawtooth'
      osc.frequency.setValueAtTime(120, t)
      osc.frequency.exponentialRampToValueAtTime(40, t + 1.2)
      g1.gain.setValueAtTime(0.15, t)
      g1.gain.exponentialRampToValueAtTime(0.001, t + 1.3)
      noise.type = 'sawtooth'
      noise.frequency.setValueAtTime(200, t)
      noise.frequency.exponentialRampToValueAtTime(60, t + 0.8)
      g2.gain.setValueAtTime(0.08, t)
      g2.gain.exponentialRampToValueAtTime(0.001, t + 1.0)
      osc.connect(g1); g1.connect(out)
      noise.connect(g2); g2.connect(out)
      osc.start(t); osc.stop(t + 1.4)
      noise.start(t); noise.stop(t + 1.1)
    } else if (tier === 8) {
      ;[392, 440, 523, 588].forEach((f, i) => {
        const osc = ctx.createOscillator()
        const g = ctx.createGain()
        osc.type = 'sine'
        osc.frequency.value = f
        const tt = t + i * 0.25
        g.gain.setValueAtTime(0.25, tt)
        g.gain.linearRampToValueAtTime(0.3, tt + 0.2)
        g.gain.exponentialRampToValueAtTime(0.001, tt + 0.8)
        osc.connect(g); g.connect(out)
        osc.start(tt); osc.stop(tt + 0.9)
      })
    } else if (tier === 9) {
      ;[392, 440, 523, 659, 784].forEach((f, i) => {
        const osc = ctx.createOscillator()
        const g = ctx.createGain()
        osc.type = i < 3 ? 'sine' : 'triangle'
        osc.frequency.value = f
        const tt = t + i * 0.2
        g.gain.setValueAtTime(0.25, tt)
        g.gain.linearRampToValueAtTime(0.3, tt + 0.15)
        g.gain.exponentialRampToValueAtTime(0.001, tt + 1.0)
        osc.connect(g); g.connect(out)
        osc.start(tt); osc.stop(tt + 1.1)
      })
    } else if (tier >= 10) {
      ;[262, 330, 392, 523, 659, 784, 1047].forEach((f, i) => {
        const osc = ctx.createOscillator()
        const g = ctx.createGain()
        osc.type = 'triangle'
        osc.frequency.value = f
        const tt = t + i * 0.18
        g.gain.setValueAtTime(0.3, tt)
        g.gain.linearRampToValueAtTime(0.35, tt + 0.15)
        g.gain.exponentialRampToValueAtTime(0.001, tt + 1.5)
        osc.connect(g); g.connect(out)
        osc.start(tt); osc.stop(tt + 1.6)
      })
      const bass = ctx.createOscillator()
      const bg = ctx.createGain()
      bass.type = 'sine'
      bass.frequency.value = 65
      bg.gain.setValueAtTime(0.2, t)
      bg.gain.exponentialRampToValueAtTime(0.001, t + 2.0)
      bass.connect(bg); bg.connect(out)
      bass.start(t); bass.stop(t + 2.2)
    }
  }
}

export const audioManager = new AudioManager()

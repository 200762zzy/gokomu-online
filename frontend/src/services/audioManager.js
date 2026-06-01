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
      this.sfxGain.gain.value = 0.5
      this.sfxGain.connect(this.ctx.destination)
      this._initialized = true
      await this._loadBGM()
    } catch (e) {
      this._pendingInit = null
    }
  }

  async _loadBGM() {
    try {
      const resp = await fetch('/audio/bgm.mp3')
      const data = await resp.arrayBuffer()
      this.bgmBuffer = await this.ctx.decodeAudioData(data)
    } catch {
      this.bgmBuffer = null
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

  async playBGM() {
    await this._ensureInit()
    if (!this.bgmBuffer) {
      await this._loadBGM()
    }
    if (!this.bgmBuffer) return
    if (this._bgmPlaying) return
    this._bgmEnabled = true
    await this._resumeCtx()
    this._scheduleBGM()
  }

  stopBGM() {
    this._bgmEnabled = false
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
    if (v) this.playBGM()
    else this.stopBGM()
  }

  get sfxEnabled() { return this._sfxEnabled }
  set sfxEnabled(v) { this._sfxEnabled = v }

  async playStone() {
    await this._ensureInit()
    if (!this._sfxEnabled || !this.ctx) return
    await this._resumeCtx()
    const osc = this.ctx.createOscillator()
    const gain = this.ctx.createGain()
    osc.type = 'sine'
    osc.frequency.setValueAtTime(180, this.ctx.currentTime)
    osc.frequency.exponentialRampToValueAtTime(80, this.ctx.currentTime + 0.12)
    gain.gain.setValueAtTime(0.4, this.ctx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.12)
    osc.connect(gain)
    gain.connect(this.sfxGain)
    osc.start()
    osc.stop(this.ctx.currentTime + 0.15)
  }

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
    gain.gain.setValueAtTime(0.25, t)
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
      gain.gain.setValueAtTime(0.3, t)
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
      gain.gain.setValueAtTime(0.2, t)
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.3)
      osc.connect(gain)
      gain.connect(this.sfxGain)
      osc.start(t)
      osc.stop(t + 0.35)
    })
  }
}

export const audioManager = new AudioManager()

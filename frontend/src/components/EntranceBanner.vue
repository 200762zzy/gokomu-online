<script setup>
import { ref, watch, onUnmounted, nextTick } from 'vue'
import { audioManager } from '../services/audioManager.js'

const props = defineProps({
  show: { type: Boolean, default: false },
  title: { type: Object, required: true },
  playerName: { type: String, default: '' },
  tier: { type: Number, default: 1 },
})

const emit = defineEmits(['done'])

const visible = ref(false)
const canvas = ref(null)
let animFrameId = null
let particles = []

const DURATION = {
  1: 2000, 2: 2000, 3: 2200, 4: 2400,
  5: 2600, 6: 2800, 7: 3000,
  8: 3500, 9: 4000, 10: 4500,
}

const TIER_COLORS = {
  8: ['#b44dff', '#ffd700', '#8b00ff'],
  9: ['#ff0080', '#ffd700', '#00ffff', '#ff6b35'],
  10: ['#ffd700', '#ffffff', '#ff8c00', '#ffdd00'],
}

watch(() => props.show, async (val) => {
  if (!val) {
    stopParticles()
    visible.value = false
    return
  }
  visible.value = true
  audioManager.playTitleSound(props.tier)
  if (props.tier >= 8) {
    await nextTick()
    startParticles()
  }
  const dur = DURATION[props.tier] || 2500
  setTimeout(() => {
    stopParticles()
    visible.value = false
    emit('done')
  }, dur)
})

function startParticles() {
  const cvs = canvas.value
  if (!cvs) return
  const ctx = cvs.getContext('2d')
  cvs.width = window.innerWidth
  cvs.height = window.innerHeight

  const colors = TIER_COLORS[props.tier] || TIER_COLORS[8]
  const count = props.tier === 10 ? 60 : props.tier === 9 ? 40 : 25
  const cx = cvs.width / 2
  const cy = cvs.height / 2

  for (let i = 0; i < count; i++) {
    const angle = Math.random() * Math.PI * 2
    const speed = 2 + Math.random() * (props.tier === 10 ? 8 : 5)
    particles.push({
      x: cx, y: cy,
      vx: Math.cos(angle) * speed,
      vy: Math.sin(angle) * speed,
      life: 1,
      decay: 0.008 + Math.random() * 0.015,
      color: colors[Math.floor(Math.random() * colors.length)],
      size: 2 + Math.random() * (props.tier === 10 ? 6 : 4),
      trail: props.tier === 10 ? [{ x: cx, y: cy }] : null,
    })
  }

  function animate() {
    if (!visible.value) return
    ctx.clearRect(0, 0, cvs.width, cvs.height)
    let alive = false
    for (const p of particles) {
      p.x += p.vx
      p.y += p.vy
      p.vx *= 0.98
      p.vy *= 0.98
      p.life -= p.decay
      if (p.life <= 0) continue
      alive = true
      if (p.trail) {
        p.trail.push({ x: p.x, y: p.y })
        if (p.trail.length > 12) p.trail.shift()
        ctx.beginPath()
        ctx.moveTo(p.trail[0].x, p.trail[0].y)
        for (let i = 1; i < p.trail.length; i++) {
          ctx.lineTo(p.trail[i].x, p.trail[i].y)
        }
        ctx.strokeStyle = p.color
        ctx.globalAlpha = p.life * 0.4
        ctx.lineWidth = p.size * 0.5
        ctx.stroke()
      }
      ctx.beginPath()
      ctx.arc(p.x, p.y, p.size * p.life, 0, Math.PI * 2)
      ctx.fillStyle = p.color
      ctx.globalAlpha = p.life
      ctx.fill()
    }
    if (alive) {
      animFrameId = requestAnimationFrame(animate)
    }
  }
  animate()
}

function stopParticles() {
  if (animFrameId) {
    cancelAnimationFrame(animFrameId)
    animFrameId = null
  }
  particles = []
}

onUnmounted(() => {
  stopParticles()
})
</script>

<template>
  <Teleport to="body">
    <div v-if="visible" class="entrance-overlay" :class="`tier-bg-${tier}`">
      <canvas v-if="tier >= 8" ref="canvas" class="entrance-canvas" />
      <div class="entrance-content" :class="`entrance-tier-${tier}`">
        <div class="entrance-icon">{{ title.icon }}</div>
        <div class="entrance-title-text">{{ title.name }}</div>
        <div class="entrance-player">{{ playerName }}</div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.entrance-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  overflow: hidden;
}

.entrance-canvas {
  position: absolute;
  top: 0; left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.entrance-content {
  position: relative;
  z-index: 1;
  text-align: center;
  animation: contentIn 0.6s ease-out;
}

@keyframes contentIn {
  0% { opacity: 0; transform: scale(0.5) translateY(30px); }
  100% { opacity: 1; transform: scale(1) translateY(0); }
}

.entrance-icon {
  font-size: 6rem;
  line-height: 1;
  margin-bottom: 12px;
  animation: iconFloat 2s ease-in-out infinite;
}

@keyframes iconFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.entrance-title-text {
  font-size: 2.2rem;
  font-weight: 800;
  letter-spacing: 4px;
  margin-bottom: 8px;
}

.entrance-player {
  font-size: 1rem;
  opacity: 0.7;
  letter-spacing: 2px;
}

/* Tier backgrounds */
.tier-bg-1 { background: radial-gradient(circle, rgba(170,170,170,0.15), rgba(0,0,0,0.85)); }
.tier-bg-2 { background: radial-gradient(circle, rgba(205,127,50,0.15), rgba(0,0,0,0.85)); }
.tier-bg-3 {
  background: radial-gradient(circle, rgba(192,192,192,0.12), rgba(0,0,0,0.85));
  position: relative;
}
.tier-bg-3::before {
  content: ''; position: absolute; inset: 0;
  background: linear-gradient(90deg, transparent, rgba(192,192,192,0.08), transparent);
  background-size: 200% 100%;
  animation: shimmerSweep 2s ease-in-out infinite;
}
.tier-bg-4 { background: radial-gradient(circle, rgba(255,215,0,0.2), rgba(0,0,0,0.85)); }
.tier-bg-5 {
  background: radial-gradient(circle, rgba(229,228,226,0.12), rgba(0,0,0,0.85));
  position: relative;
}
.tier-bg-5::before {
  content: ''; position: absolute; inset: 0;
  background: linear-gradient(135deg, transparent 30%, rgba(229,228,226,0.06) 50%, transparent 70%);
  background-size: 200% 200%;
  animation: shimmerSweep 3s ease-in-out infinite;
}
.tier-bg-6 {
  background: radial-gradient(circle, rgba(0,255,255,0.15), rgba(0,0,0,0.85));
  position: relative;
}
.tier-bg-6::before {
  content: ''; position: absolute; inset: 0;
  background: linear-gradient(45deg, transparent, rgba(0,255,255,0.05), transparent);
  background-size: 300% 100%;
  animation: shimmerSweep 2.5s linear infinite;
}
.tier-bg-7 { background: radial-gradient(circle, rgba(255,107,53,0.2), rgba(0,0,0,0.85)); }
.tier-bg-8 { background: radial-gradient(circle, rgba(180,77,255,0.15), rgba(0,0,0,0.85)); }
.tier-bg-9 { background: radial-gradient(circle, rgba(255,0,128,0.2), rgba(0,0,0,0.85)); }
.tier-bg-10 { background: radial-gradient(circle, rgba(255,215,0,0.3), rgba(0,0,0,0.85)); }

@keyframes shimmerSweep {
  0% { background-position: 0% 0%; }
  100% { background-position: 200% 0%; }
}

/* Tier text colors */
.entrance-tier-1 .entrance-title-text { color: #aaa; }
.entrance-tier-2 .entrance-title-text { color: #cd7f32; }
.entrance-tier-3 .entrance-title-text { color: #c0c0c0; }
.entrance-tier-4 .entrance-title-text { color: #ffd700; }
.entrance-tier-5 .entrance-title-text { color: #e5e4e2; }
.entrance-tier-6 .entrance-title-text { color: #00ffff; text-shadow: 0 0 20px rgba(0,255,255,0.4); }
.entrance-tier-7 .entrance-title-text { color: #ff6b35; text-shadow: 0 0 20px rgba(255,107,53,0.4); }
.entrance-tier-8 .entrance-title-text { color: #b44dff; text-shadow: 0 0 30px rgba(180,77,255,0.5); }
.entrance-tier-9 .entrance-title-text {
  color: #ff0080;
  text-shadow: 0 0 30px rgba(255,0,128,0.5);
  animation: rainbowText 2s linear infinite;
}
.entrance-tier-10 .entrance-title-text {
  color: #ffd700;
  text-shadow: 0 0 40px rgba(255,215,0,0.6), 0 0 80px rgba(255,215,0,0.3);
  animation: legendaryGlow 1.5s ease-in-out infinite;
}

@keyframes rainbowText {
  0% { filter: hue-rotate(0deg); }
  100% { filter: hue-rotate(360deg); }
}

@keyframes legendaryGlow {
  0%, 100% { text-shadow: 0 0 40px rgba(255,215,0,0.6), 0 0 80px rgba(255,215,0,0.3); }
  50% { text-shadow: 0 0 60px rgba(255,215,0,0.8), 0 0 120px rgba(255,215,0,0.5); }
}
</style>

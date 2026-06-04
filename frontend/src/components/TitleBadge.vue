<script setup>
const props = defineProps({
  title: { type: Object, required: true },
  animate: { type: Boolean, default: false },
  size: { type: String, default: 'md' },
})

const emit = defineEmits(['animation-end'])

function onAnimationEnd() {
  emit('animation-end')
}
</script>

<template>
  <span
    :class="['title-badge', `size-${size}`, title.cssClass || '', { animating: animate }]"
    :title="title.name"
    @animationend="onAnimationEnd"
  >
    <span class="title-icon">{{ title.icon }}</span>
    <span class="title-name">{{ title.name }}</span>
  </span>
</template>

<style scoped>
.title-badge {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-weight: 600;
  border-radius: 4px;
  white-space: nowrap;
  transition: all 0.3s;
}
.size-sm { font-size: 0.75rem; padding: 1px 5px; }
.size-md { font-size: 0.85rem; padding: 2px 8px; }
.size-lg { font-size: 1rem; padding: 3px 10px; }

.title-icon { font-size: 1.1em; line-height: 1; }
.title-name { line-height: 1; }

.tier-1 { color: #aaa; background: rgba(255,255,255,0.04); }
.tier-2 { color: #cd7f32; background: rgba(205,127,50,0.12); }
.tier-3 { color: #c0c0c0; background: rgba(192,192,192,0.12); }
.tier-4 { color: #ffd700; background: rgba(255,215,0,0.12); }
.tier-5 { color: #e5e4e2; background: rgba(229,228,226,0.10); }
.tier-6 { color: #00ffff; background: rgba(0,255,255,0.08); }
.tier-7 { color: #ff6b35; background: rgba(255,107,53,0.12); }
.tier-8 { color: #b44dff; background: rgba(180,77,255,0.12); }
.tier-9 {
  color: #ff0080;
  background: linear-gradient(135deg, rgba(255,0,128,0.12), rgba(255,215,0,0.12));
}
.tier-10 {
  color: #ffd700;
  background: linear-gradient(135deg, rgba(255,215,0,0.15), rgba(255,255,255,0.08));
  text-shadow: 0 0 8px rgba(255,215,0,0.4);
}

/* Entrance animations */
.animating {
  animation-duration: 1.2s;
  animation-fill-mode: forwards;
}
.tier-1.animating { animation-name: fadeIn; }
.tier-2.animating { animation-name: glowIn; }
.tier-3.animating { animation-name: shimmerIn; }
.tier-4.animating { animation-name: goldPulse; }
.tier-5.animating { animation-name: platinaShine; }
.tier-6.animating { animation-name: sparkleIn; }
.tier-7.animating { animation-name: flameIn; }
.tier-8.animating { animation-name: royalRise; }
.tier-9.animating { animation-name: trophyReveal; }
.tier-10.animating { animation-name: legendaryBurst; }

@keyframes fadeIn {
  0% { opacity: 0; transform: scale(0.8); }
  100% { opacity: 1; transform: scale(1); }
}
@keyframes glowIn {
  0% { opacity: 0; box-shadow: 0 0 0 0 rgba(205,127,50,0); }
  50% { opacity: 1; box-shadow: 0 0 12px 2px rgba(205,127,50,0.4); }
  100% { opacity: 1; box-shadow: 0 0 0 0 rgba(205,127,50,0); }
}
@keyframes shimmerIn {
  0% { opacity: 0; background-position: -100% 0; }
  50% { opacity: 1; }
  100% { opacity: 1; background-position: 200% 0; }
}
@keyframes goldPulse {
  0% { opacity: 0; transform: scale(0.5); box-shadow: 0 0 0 0 rgba(255,215,0,0.3); }
  40% { opacity: 1; transform: scale(1.15); box-shadow: 0 0 20px 4px rgba(255,215,0,0.6); }
  100% { opacity: 1; transform: scale(1); box-shadow: 0 0 0 0 rgba(255,215,0,0); }
}
@keyframes platinaShine {
  0% { opacity: 0; transform: scale(0.6); filter: brightness(0.5); }
  40% { opacity: 1; transform: scale(1.1); filter: brightness(1.5); box-shadow: 0 0 25px 5px rgba(229,228,226,0.5); }
  100% { opacity: 1; transform: scale(1); filter: brightness(1); box-shadow: 0 0 0 0 rgba(229,228,226,0); }
}
@keyframes sparkleIn {
  0% { opacity: 0; transform: rotateY(90deg); }
  50% { opacity: 1; transform: rotateY(0); box-shadow: 0 0 20px 4px rgba(0,255,255,0.5); }
  100% { opacity: 1; box-shadow: 0 0 0 0 rgba(0,255,255,0); }
}
@keyframes flameIn {
  0% { opacity: 0; transform: scale(0.3); }
  30% { opacity: 1; transform: scale(1.2); box-shadow: 0 0 30px 6px rgba(255,107,53,0.6); }
  100% { opacity: 1; transform: scale(1); box-shadow: 0 0 0 0 rgba(255,107,53,0); }
}
@keyframes royalRise {
  0% { opacity: 0; transform: translateY(30px) scale(0.5); }
  30% { opacity: 1; transform: translateY(-5px) scale(1.1); box-shadow: 0 0 30px 6px rgba(180,77,255,0.5); }
  60% { transform: translateY(2px) scale(1); }
  100% { opacity: 1; transform: translateY(0) scale(1); box-shadow: 0 0 0 0 rgba(180,77,255,0); }
}
@keyframes trophyReveal {
  0% { opacity: 0; transform: scale(0) rotate(-180deg); }
  30% { opacity: 1; transform: scale(1.3) rotate(10deg); box-shadow: 0 0 40px 8px rgba(255,0,128,0.6); }
  60% { transform: scale(0.95) rotate(-3deg); }
  100% { opacity: 1; transform: scale(1) rotate(0); box-shadow: 0 0 0 0 rgba(255,0,128,0); }
}
@keyframes legendaryBurst {
  0% { opacity: 0; transform: scale(0); filter: hue-rotate(0deg); }
  20% { opacity: 1; transform: scale(1.4); filter: hue-rotate(120deg); box-shadow: 0 0 60px 12px rgba(255,215,0,0.8); }
  50% { transform: scale(0.9); filter: hue-rotate(240deg); }
  80% { transform: scale(1.05); box-shadow: 0 0 30px 6px rgba(255,215,0,0.4); }
  100% { opacity: 1; transform: scale(1); filter: hue-rotate(360deg); box-shadow: 0 0 0 0 rgba(255,215,0,0); }
}
</style>

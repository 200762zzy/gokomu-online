<script setup>
import { ref, computed, watch, onMounted } from 'vue'

const props = defineProps({
  value: { type: Number, default: null },
  rolling: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['roll'])

const showDice = ref(false)
const animating = ref(false)
const displayValue = ref(1)
const rotationX = ref(0)
const rotationY = ref(0)

const faceClass = computed(() => `face-${displayValue.value}`)

function roll() {
  if (props.disabled || animating.value) return
  emit('roll')
}

watch(() => props.rolling, (val) => {
  if (val) {
    animating.value = true
    const spins = 3 + Math.floor(Math.random() * 3)
    const finalVal = props.value || Math.floor(Math.random() * 6) + 1
    rotationX.value = spins * 360 + (finalVal === 1 ? 0 : finalVal === 6 ? 180 : finalVal === 2 ? -90 : finalVal === 5 ? 90 : finalVal === 3 ? 0 : 0)
    rotationY.value = spins * 360 + (finalVal === 1 ? 0 : finalVal === 6 ? 0 : finalVal === 2 ? 0 : finalVal === 5 ? 0 : finalVal === 3 ? 90 : -90)
    setTimeout(() => {
      displayValue.value = finalVal
      animating.value = false
    }, 800)
  }
})

watch(() => props.value, (val) => {
  if (val !== null && !props.rolling) {
    displayValue.value = val
    showDice.value = true
  }
})

onMounted(() => {
  if (props.value !== null) {
    displayValue.value = props.value
    showDice.value = true
  }
})
</script>

<template>
  <div class="dice-container" :class="{ disabled }" @click="roll">
    <div class="dice" :class="{ animating, rolling: props.rolling }" :style="{
      transform: `rotateX(${rotationX}deg) rotateY(${rotationY}deg)`,
    }">
      <div class="dice-face front">
        <span class="dot c1"></span>
        <span class="dot c2"></span>
        <span class="dot c3"></span>
        <span class="dot c4"></span>
        <span class="dot c5"></span>
        <span class="dot c6"></span>
      </div>
      <div class="dice-face back">
        <span class="dot c1"></span>
        <span class="dot c2"></span>
        <span class="dot c3"></span>
        <span class="dot c4"></span>
        <span class="dot c5"></span>
        <span class="dot c6"></span>
        <span class="dot c7"></span>
      </div>
      <div class="dice-face right">
        <span class="dot c1"></span>
        <span class="dot c2"></span>
        <span class="dot c3"></span>
        <span class="dot c4"></span>
        <span class="dot c5"></span>
        <span class="dot c6"></span>
        <span class="dot c7"></span>
        <span class="dot c8"></span>
        <span class="dot c9"></span>
        <span class="dot c10"></span>
      </div>
      <div class="dice-face left">
        <span class="dot c1"></span>
        <span class="dot c2"></span>
        <span class="dot c3"></span>
        <span class="dot c4"></span>
        <span class="dot c5"></span>
        <span class="dot c6"></span>
        <span class="dot c7"></span>
        <span class="dot c8"></span>
        <span class="dot c9"></span>
      </div>
      <div class="dice-face top">
        <span class="dot c1"></span>
        <span class="dot c2"></span>
        <span class="dot c3"></span>
        <span class="dot c4"></span>
        <span class="dot c5"></span>
        <span class="dot c6"></span>
        <span class="dot c7"></span>
        <span class="dot c8"></span>
        <span class="dot c9"></span>
      </div>
      <div class="dice-face bottom">
        <span class="dot c1"></span>
        <span class="dot c2"></span>
        <span class="dot c3"></span>
        <span class="dot c4"></span>
        <span class="dot c5"></span>
        <span class="dot c6"></span>
        <span class="dot c7"></span>
        <span class="dot c8"></span>
        <span class="dot c9"></span>
        <span class="dot c10"></span>
        <span class="dot c11"></span>
      </div>
    </div>
    <div class="dice-hint" v-if="!disabled && !props.rolling">点击掷骰</div>
  </div>
</template>

<style scoped>
.dice-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  perspective: 600px;
  cursor: pointer;
  user-select: none;
}
.dice-container.disabled {
  cursor: not-allowed;
  opacity: 0.6;
}
.dice {
  width: 64px;
  height: 64px;
  position: relative;
  transform-style: preserve-3d;
  transition: transform 0.1s;
}
.dice.animating {
  transition: transform 0.8s cubic-bezier(0.22, 1, 0.36, 1);
}
.dice.rolling {
  animation: shake 0.15s ease infinite;
}
@keyframes shake {
  0%, 100% { translate: 0 0; }
  25% { translate: -3px 2px; }
  75% { translate: 3px -2px; }
}
.dice-face {
  position: absolute;
  width: 64px;
  height: 64px;
  background: #fff;
  border: 2px solid #ccc;
  border-radius: 10px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: repeat(3, 1fr);
  place-items: center;
  padding: 6px;
  box-sizing: border-box;
  backface-visibility: hidden;
}
.front { transform: translateZ(32px); }
.back { transform: rotateX(180deg) translateZ(32px); }
.right { transform: rotateY(90deg) translateZ(32px); }
.left { transform: rotateY(-90deg) translateZ(32px); }
.top { transform: rotateX(90deg) translateZ(32px); }
.bottom { transform: rotateX(-90deg) translateZ(32px); }

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #222;
}

/* Face 1 - center only */
.c1 { grid-column: 2; grid-row: 2; }
/* Face 2 */
.c2:nth-child(2) { grid-column: 1; grid-row: 1; } .c2:nth-child(2) + .c2 { grid-column: 3; grid-row: 3; }
/* Face 3 */
.c3:nth-child(2) { grid-column: 1; grid-row: 1; } .c3:nth-child(2) + .c3 { grid-column: 2; grid-row: 2; } .c3:nth-child(2) + .c3 + .c3 { grid-column: 3; grid-row: 3; }
/* Face 4 */
.c4:nth-child(2) { grid-column: 1; grid-row: 1; } .c4:nth-child(2) + .c4 { grid-column: 3; grid-row: 1; } .c4:nth-child(2) + .c4 + .c4 { grid-column: 1; grid-row: 3; } .c4:nth-child(2) + .c4 + .c4 + .c4 { grid-column: 3; grid-row: 3; }
/* Face 5 - 4 corners + center */
.c5:nth-child(2) { grid-column: 1; grid-row: 1; } .c5:nth-child(2) + .c5 { grid-column: 3; grid-row: 1; } .c5:nth-child(2) + .c5 + .c5 { grid-column: 1; grid-row: 3; } .c5:nth-child(2) + .c5 + .c5 + .c5 { grid-column: 3; grid-row: 3; } .c5:nth-child(2) + .c5 + .c5 + .c5 + .c5 { grid-column: 2; grid-row: 2; }
/* Face 6 - 2 columns of 3 */
.c6:nth-child(2) { grid-column: 1; grid-row: 1; } .c6:nth-child(2) + .c6 { grid-column: 3; grid-row: 1; } .c6:nth-child(2) + .c6 + .c6 { grid-column: 1; grid-row: 2; } .c6:nth-child(2) + .c6 + .c6 + .c6 { grid-column: 3; grid-row: 2; } .c6:nth-child(2) + .c6 + .c6 + .c6 + .c6 { grid-column: 1; grid-row: 3; } .c6:nth-child(2) + .c6 + .c6 + .c6 + .c6 + .c6 { grid-column: 3; grid-row: 3; }

.dice-hint {
  font-size: 0.8rem;
  color: #888;
  animation: pulse-hint 1.5s ease infinite alternate;
}
@keyframes pulse-hint {
  from { opacity: 0.5; }
  to { opacity: 1; }
}
</style>

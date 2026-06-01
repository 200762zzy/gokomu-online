<script setup>
defineProps({
  currentTurn: String,
  gameOver: Boolean,
  winner: String,
  gameResult: String,
  blackMoveCount: Number,
  whiteMoveCount: Number,
})
</script>

<template>
  <div class="game-info">
    <div v-if="!gameOver" class="info-row">
      <span class="label">当前回合</span>
      <span class="value" :class="currentTurn">
        <span v-if="currentTurn === 'black'" class="stone black">●</span>
        <span v-else class="stone white">○</span>
        {{ currentTurn === 'black' ? '黑方' : '白方' }}
      </span>
    </div>
    <div v-if="gameOver" class="info-row game-over">
      <span class="label">结果</span>
      <span class="value winner">
        <template v-if="gameResult === 'draw'">平局</template>
        <template v-else-if="gameResult === 'resign_black'">白方胜（黑方认负）</template>
        <template v-else-if="gameResult === 'resign_white'">黑方胜（白方认负）</template>
        <template v-else-if="winner === 'black'">黑方获胜！</template>
        <template v-else-if="winner === 'white'">白方获胜！</template>
      </span>
    </div>
    <div class="info-row">
      <span class="label">黑方</span>
      <span class="value">第 {{ blackMoveCount }} 手</span>
    </div>
    <div class="info-row">
      <span class="label">白方</span>
      <span class="value">第 {{ whiteMoveCount }} 手</span>
    </div>
  </div>
</template>

<style scoped>
.game-info {
  background: rgba(22, 33, 62, 0.85);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  padding: 16px;
  width: 100%;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #1a1a3e;
}

.info-row:last-child {
  border-bottom: none;
}

.label {
  color: #888;
  font-size: 0.85rem;
}

.value {
  font-size: 0.95rem;
  font-weight: 600;
}

.value.black {
  color: #333;
}

.value.white {
  color: #ccc;
}

.stone {
  display: inline-block;
  width: 20px;
  text-align: center;
}

.stone.black {
  color: #111;
  text-shadow: 0 0 2px rgba(255,255,255,0.3);
}

.stone.white {
  color: #ddd;
  text-shadow: 0 0 2px rgba(0,0,0,0.3);
}

.game-over {
  background: #533483;
  border-radius: 6px;
  padding: 8px 12px;
  margin: 4px -12px;
}

.winner {
  color: #ffd700;
  font-size: 1rem;
}
</style>

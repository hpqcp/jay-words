<template>
  <div class="racing-page">
    <div v-if="words.length === 0 && !isPlaying && !gameOver" class="empty">
      <p>该章节暂无单词</p>
      <router-link to="/">返回首页</router-link>
    </div>

    <template v-else-if="showSetup">
      <div class="card setup-card">
        <h2>🏎️ 单词赛车</h2>
        <p class="setup-desc">选择单词下落速度：</p>
        <div class="speed-options">
          <button
            v-for="opt in speedOptions" :key="opt.value"
            class="speed-btn"
            :class="{ active: speedLevel === opt.value }"
            @click="speedLevel = opt.value"
          >
            <span class="speed-icon">{{ opt.icon }}</span>
            <span class="speed-label">{{ opt.label }}</span>
            <span class="speed-ms">{{ opt.ms }}ms</span>
          </button>
        </div>
        <button class="btn-primary start-btn" @click="startGame">开始比赛 🏁</button>
      </div>
    </template>

    <template v-else-if="gameOver">
      <div class="card result-card">
        <h2>🏁 比赛结束！</h2>
        <p class="result-big">{{ score }} 分</p>
        <div class="result-stats">
          <span>答对 <strong>{{ correct }}</strong></span>
          <span>错过 <strong>{{ missed }}</strong></span>
          <span>正确率 <strong>{{ correct + missed > 0 ? Math.round(correct / (correct + missed) * 100) : 0 }}%</strong></span>
        </div>
        <div class="result-actions">
          <button class="btn-primary" @click="showSetup = true; gameOver = false">再来一局</button>
          <router-link to="/" class="btn-ghost" style="padding:8px 20px;border-radius:8px;text-decoration:none">返回首页</router-link>
        </div>
      </div>
    </template>

    <template v-else>
      <div class="hud">
        <span class="hud-score">⭐ {{ score }}</span>
        <span v-if="combo >= 2" class="hud-combo">🔥 {{ combo }}连击</span>
        <span class="hud-progress">{{ currentIndex + 1 }}/{{ words.length }}</span>
      </div>

      <div class="track" ref="trackRef">
        <div
          class="card falling-card"
          :class="{ danger: position > 60, correct: feedback === 'correct', missed: feedback === 'missed' }"
          :style="{ top: position + '%' }"
        >
          {{ words[currentIndex].chinese }}
        </div>
        <div v-if="feedback" class="feedback-overlay" :class="feedback">
          <span v-if="feedback === 'correct'" class="fb-text">✅ +{{ lastScore }}</span>
          <span v-else-if="feedback === 'missed'" class="fb-text miss-text">❌ {{ words[currentIndex].english }}</span>
        </div>
        <div class="danger-line"></div>
      </div>

      <div class="input-row">
        <input
          ref="inputRef"
          v-model="input"
          class="racing-input"
          placeholder="输入英文..."
          :disabled="!!feedback"
          @keyup.enter="submitInput"
        />
        <button class="btn-primary" @click="submitInput" :disabled="!input.trim() || !!feedback">确认</button>
      </div>
    </template>
  </div>
</template>

<script>
import { ref, onMounted, nextTick, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api/index.js'

export default {
  name: 'Racing',
  setup() {
    const route = useRoute()
    const words = ref([])
    const currentIndex = ref(0)
    const position = ref(0)
    const score = ref(0)
    const combo = ref(0)
    const correct = ref(0)
    const missed = ref(0)
    const speed = ref(5000)
    const input = ref('')
    const feedback = ref(null)
    const lastScore = ref(0)
    const isPlaying = ref(false)
    const gameOver = ref(false)
    const showSetup = ref(true)
    const speedLevel = ref('medium')
    const trackRef = ref(null)
    const inputRef = ref(null)
    let animId = null
    let startTime = 0

    const speedOptions = [
      { value: 'slow',  icon: '🐢', label: '慢速', ms: 10000 },
      { value: 'medium', icon: '🚗', label: '中速', ms: 8000 },
      { value: 'fast',  icon: '🏎️', label: '快速', ms: 5000 },
      { value: 'insane', icon: '🚀', label: '极速', ms: 3000 },
    ]

    const loadWords = async () => {
      const sectionId = parseInt(route.query.sectionId)
      if (!sectionId) return
      let arr = await api.getSectionWords(sectionId)
      for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]]
      }
      words.value = arr
    }

    const startGame = () => {
      const map = { slow: 10000, medium: 8000, fast: 5000, insane: 3000 }
      speed.value = map[speedLevel.value] || 5000
      showSetup.value = false
      gameOver.value = false
      currentIndex.value = 0
      position.value = 0
      score.value = 0
      combo.value = 0
      correct.value = 0
      missed.value = 0
      feedback.value = null
      input.value = ''
      isPlaying.value = true
      nextTick(() => {
        startTime = performance.now()
        gameLoop()
        if (inputRef.value) inputRef.value.focus()
      })
    }

    const gameLoop = () => {
      if (!isPlaying.value) return
      const elapsed = performance.now() - startTime
      const pct = Math.min((elapsed / speed.value) * 100, 100)
      position.value = pct

      if (pct >= 100) {
        handleMissed()
        return
      }

      animId = requestAnimationFrame(gameLoop)
    }

    const handleMissed = () => {
      feedback.value = 'missed'
      missed.value++
      combo.value = 0
      api.submitRecord(words.value[currentIndex.value].id, 'racing', 0)
      setTimeout(() => nextWord(), 800)
    }

    const submitInput = () => {
      if (feedback.value || !input.value.trim() || !isPlaying.value) return
      const word = words.value[currentIndex.value]
      const correctAnswer = input.value.trim().toLowerCase() === word.english.toLowerCase()

      if (!correctAnswer) {
        // Wrong attempt—shake and clear, no record
        feedback.value = 'wrong'
        setTimeout(() => {
          feedback.value = null
          input.value = ''
          if (inputRef.value) inputRef.value.focus()
        }, 350)
        return
      }

      // Correct
      isPlaying.value = false
      if (animId) cancelAnimationFrame(animId)
      correct.value++
      combo.value++
      const remaining = 1 - position.value / 100
      const bonus = Math.round(remaining * 10)
      const multiplier = combo.value >= 6 ? 2 : combo.value >= 3 ? 1.5 : 1
      const pts = Math.round((10 + bonus) * multiplier)
      lastScore.value = pts
      score.value += pts
      feedback.value = 'correct'
      api.submitRecord(word.id, 'racing', 1)

      // Speed up every 3 correct
      if (correct.value % 3 === 0) speed.value = Math.max(1500, speed.value - 400)

      setTimeout(() => nextWord(), 600)
    }

    const nextWord = () => {
      const next = currentIndex.value + 1
      if (next >= words.value.length) {
        gameOver.value = true
        isPlaying.value = false
        return
      }
      currentIndex.value = next
      position.value = 0
      feedback.value = null
      input.value = ''
      isPlaying.value = true
      startTime = performance.now()
      gameLoop()
      nextTick(() => {
        if (inputRef.value) inputRef.value.focus()
      })
    }

    onMounted(() => { loadWords() })
    onUnmounted(() => { if (animId) cancelAnimationFrame(animId) })

    return { words, currentIndex, position, score, combo, correct, missed, input, feedback, lastScore, isPlaying, gameOver, showSetup, speedLevel, trackRef, inputRef, speedOptions, startGame, submitInput }
  }
}
</script>

<style scoped>
.racing-page { max-width: 500px; margin: 0 auto; text-align: center; }
.empty { text-align: center; padding: 40px; color: #999; }
.empty a { color: #4f46e5; }

.hud { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; font-size: 16px; }
.hud-score { font-weight: bold; color: #f59e0b; }
.hud-combo { color: #ef4444; font-weight: bold; animation: pulse 0.6s infinite; }
.hud-progress { color: #888; }

.track {
  position: relative; height: 360px; background: #f8faff;
  border-radius: 16px; overflow: hidden; border: 2px solid #e0e7ff; margin-bottom: 16px;
}
.danger-line {
  position: absolute; bottom: 0; left: 0; right: 0; height: 40px;
  background: repeating-linear-gradient(-45deg, transparent, transparent 8px, #fee2e2 8px, #fee2e2 16px);
  border-top: 2px solid #ef4444;
}
.falling-card {
  position: absolute; left: 10%; right: 10%; padding: 16px;
  font-size: 28px; font-weight: bold; color: #333;
  background: #fff; border-radius: 16px;
  box-shadow: 0 4px 16px rgba(79,70,229,0.15);
  transition: background 0.2s, border-color 0.2s;
  z-index: 2; text-align: center;
}
.falling-card.danger { border: 3px solid #ef4444; background: #fef2f2; color: #ef4444; }
.falling-card.correct { border: 3px solid #22c55e; background: #f0fdf4; }
.falling-card.missed { opacity: 0; transition: opacity 0.3s; }

.feedback-overlay {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
  z-index: 5; pointer-events: none;
}
.fb-text { font-size: 28px; font-weight: bold; white-space: nowrap; }
.miss-text { font-size: 20px; color: #ef4444; }

.input-row { display: flex; gap: 12px; }
.racing-input {
  flex: 1; font-size: 22px; text-align: center; padding: 12px; border: 3px solid #e0e7ff;
  border-radius: 12px; outline: none;
}
.racing-input:focus { border-color: #4f46e5; }

.setup-card { text-align: center; padding: 32px; margin-top: 20px; }
.setup-card h2 { font-size: 28px; margin-bottom: 8px; }
.setup-desc { color: #888; margin-bottom: 20px; }
.speed-options { display: flex; gap: 12px; margin-bottom: 24px; }
.speed-btn {
  flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px;
  padding: 16px 8px; border: 3px solid #e0e7ff; border-radius: 16px;
  background: #fff; cursor: pointer; transition: all 0.2s;
}
.speed-btn:hover { border-color: #4f46e5; background: #f0f4ff; }
.speed-btn.active { border-color: #4f46e5; background: #ede9fe; }
.speed-icon { font-size: 28px; }
.speed-label { font-size: 15px; font-weight: 600; color: #333; }
.speed-ms { font-size: 12px; color: #999; }
.start-btn { font-size: 20px; padding: 14px 48px; }
.result-card { text-align: center; padding: 40px; margin-top: 40px; }
.result-big { font-size: 56px; font-weight: bold; color: #4f46e5; margin: 12px 0; }
.result-stats { display: flex; justify-content: center; gap: 24px; margin: 16px 0; font-size: 15px; color: #666; }
.result-actions { display: flex; gap: 16px; justify-content: center; margin-top: 24px; }

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.15); }
}
</style>

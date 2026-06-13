<template>
  <div class="completion-page">
    <div v-if="words.length === 0" class="empty">
      <p>该章节暂无单词</p>
      <router-link to="/">返回首页</router-link>
    </div>
    <template v-else>
      <div class="progress-info">
        <span>{{ current + 1 }} / {{ words.length }}</span>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: ((current + 1) / words.length * 100) + '%' }"></div>
        </div>
      </div>

      <div v-if="current >= words.length" class="card result-card">
        <h2>🎉 全部完成！</h2>
        <p class="result-text">共 {{ words.length }} 词</p>
        <div class="result-actions">
          <button class="btn-primary" @click="restart">重新学习</button>
          <router-link to="/" class="btn-ghost" style="padding: 8px 20px; border-radius: 8px; text-decoration: none;">返回首页</router-link>
        </div>
      </div>

      <template v-else>
        <div class="word-label">第 {{ current + 1 }} / {{ words.length }} 词 · 补全单词</div>

        <div class="card hint-card">
          <div class="chinese-hint">{{ words[current].chinese }}</div>
          <button class="btn-ghost speak-btn" @click="speak">🔊 听发音</button>
        </div>

        <div class="blank-display">
          <span v-for="(ch, i) in blankDisplay" :key="i" class="blank-char" :class="{ hidden: blanks.includes(i), correct: revealed.has(i) }">
            {{ blanks.includes(i) ? (revealed.has(i) ? words[current].english[i] : '_') : ch }}
          </span>
        </div>

        <div class="input-area">
          <input
            ref="inputRef"
            v-model="userInput"
            class="spell-input"
            placeholder="输入完整单词..."
            @keyup.enter="submitInput"
          />
          <button class="btn-primary" @click="submitInput" :disabled="!userInput.trim()">
            {{ feedback && feedback.type === 'correct' ? '下一词 →' : '确认' }}
          </button>
        </div>

        <div v-if="feedback" class="feedback" :class="feedback.type">
          <template v-if="feedback.type === 'correct'">✅ 正确！</template>
          <template v-else-if="feedback.type === 'wrong'">
            ❌ 错误，正确答案是：<strong>{{ feedback.correctAnswer }}</strong>
          </template>
        </div>
      </template>
    </template>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api/index.js'

function pickBlanks(word) {
  const len = word.length
  if (len <= 2) return len <= 1 ? [] : [1]
  const count = len <= 3 ? 1 : (Math.random() < 0.5 ? 1 : 2)
  const positions = []
  const pool = []
  for (let i = 1; i < len; i++) pool.push(i)
  for (let i = pool.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [pool[i], pool[j]] = [pool[j], pool[i]]
  }
  for (let i = 0; i < count && i < pool.length; i++) positions.push(pool[i])
  return positions.sort((a, b) => a - b)
}

export default {
  name: 'Completion',
  setup() {
    const route = useRoute()
    const words = ref([])
    const current = ref(0)
    const userInput = ref('')
    const feedback = ref(null)
    const inputRef = ref(null)
    const blanks = ref([])
    const revealed = ref(new Set())

    const blankDisplay = computed(() => {
      if (!words.value[current.value]) return []
      return words.value[current.value].english.split('')
    })

    const loadWords = async () => {
      const sectionId = parseInt(route.query.sectionId)
      const wordId = parseInt(route.query.wordId)
      let arr
      if (sectionId) {
        arr = await api.getSectionWords(sectionId)
      } else if (wordId) {
        arr = [await api.getWord(wordId)]
      } else {
        return
      }
      for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]]
      }
      words.value = arr
      current.value = 0
      userInput.value = ''
      feedback.value = null
      blanks.value = words.value.length > 0 ? pickBlanks(words.value[0].english) : []
      revealed.value = new Set()
    }

    const submitInput = async () => {
      if (!userInput.value.trim()) return
      if (feedback.value && feedback.value.type === 'correct') {
        advance()
        return
      }

      const word = words.value[current.value]
      const correct = userInput.value.trim().toLowerCase() === word.english.toLowerCase()

      if (!correct) {
        feedback.value = { type: 'wrong', correctAnswer: word.english }
        await api.submitAnswer(word.id, userInput.value)
        api.submitRecord(word.id, 'completion', 0)
        return
      }

      feedback.value = { type: 'correct' }
      api.submitRecord(word.id, 'completion', 1)
      const r = new Set(revealed.value)
      blanks.value.forEach(i => r.add(i))
      revealed.value = r
    }

    const advance = () => {
      const next = current.value + 1
      if (next < words.value.length) {
        current.value = next
        userInput.value = ''
        feedback.value = null
        blanks.value = pickBlanks(words.value[next].english)
        revealed.value = new Set()
        nextTick(() => { if (inputRef.value) inputRef.value.focus() })
      } else {
        current.value = next
      }
    }

    const speak = () => {
      if (!window.speechSynthesis) return
      const word = words.value[current.value]
      if (!word) return
      const utter = new SpeechSynthesisUtterance(word.english)
      utter.lang = 'en-US'
      utter.rate = 0.9
      speechSynthesis.speak(utter)
    }

    const restart = () => {
      current.value = 0
      userInput.value = ''
      feedback.value = null
      blanks.value = words.value.length > 0 ? pickBlanks(words.value[0].english) : []
      revealed.value = new Set()
    }

    watch(() => route.query.sectionId, loadWords)
    onMounted(() => {
      loadWords()
    })

    return { words, current, userInput, feedback, inputRef, blankDisplay, blanks, revealed, submitInput, advance, speak, restart }
  }
}
</script>

<style scoped>
.completion-page { max-width: 500px; margin: 0 auto; text-align: center; }
.empty { text-align: center; padding: 40px; color: #999; }
.empty a { color: #4f46e5; }
.progress-info { margin-bottom: 8px; color: #666; font-size: 14px; }
.progress-bar { height: 6px; background: #e0e7ff; border-radius: 3px; margin-top: 6px; overflow: hidden; }
.progress-fill { height: 100%; background: #f59e0b; transition: width 0.3s; border-radius: 3px; }
.word-label { font-size: 13px; color: #999; margin-bottom: 12px; }
.hint-card { margin-bottom: 16px; padding: 20px; }
.chinese-hint { font-size: 28px; font-weight: bold; color: #333; margin-bottom: 8px; }
.speak-btn { font-size: 15px; }
.blank-display {
  display: flex; justify-content: center; gap: 6px; flex-wrap: wrap;
  margin: 24px 0; padding: 24px; background: #fff; border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}
.blank-char {
  font-size: 36px; font-weight: bold; font-family: 'Courier New', monospace;
  width: 36px; text-align: center; color: #333;
}
.blank-char.hidden { color: #4f46e5; border-bottom: 3px solid #4f46e5; }
.blank-char.correct { color: #22c55e; border-bottom-color: #22c55e; }
.input-area { display: flex; gap: 12px; margin-top: 16px; justify-content: center; }
.spell-input { flex: 1; max-width: 300px; font-size: 20px; text-align: center; padding: 12px; border-width: 3px; }
.feedback { font-size: 20px; margin-top: 12px; padding: 8px; border-radius: 8px; }
.feedback.correct { color: #22c55e; }
.feedback.wrong { color: #ef4444; }
.result-card { text-align: center; padding: 40px; margin-top: 40px; }
.result-text { font-size: 18px; color: #666; margin: 16px 0; }
.result-actions { display: flex; gap: 16px; justify-content: center; margin-top: 24px; }
</style>

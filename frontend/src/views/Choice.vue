<template>
  <div class="choice-page">
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
        <p class="result-text">共 {{ words.length }} 题</p>
        <div class="result-actions">
          <button class="btn-primary" @click="restart">重新学习</button>
          <router-link to="/" class="btn-ghost" style="padding: 8px 20px; border-radius: 8px; text-decoration: none;">返回首页</router-link>
        </div>
      </div>

      <template v-else>
        <div class="word-label">
          第 {{ current + 1 }} / {{ words.length }} 词
          <template v-if="phase === 'type'"> · 手动输入第 {{ typePassCount + 1 }}/3 遍</template>
          <template v-else> · 选择正确单词</template>
        </div>

        <div class="card hint-card">
          <div class="chinese-word">{{ words[current].chinese }}</div>
          <button class="btn-ghost speak-btn" @click="speak">🔊 听发音</button>
        </div>

        <!-- Choice phase: 4 options -->
        <template v-if="phase === 'choice'">
          <div class="options">
            <button
              v-for="(opt, i) in shuffledOptions"
              :key="i"
              class="option-btn"
              :class="optionClass(opt)"
              :disabled="!!feedback"
              @click="selectOption(opt)"
            >
              <span class="option-label">{{ optionLetters[i] }}</span>
              {{ opt }}
            </button>
          </div>

          <div v-if="feedback" class="feedback" :class="feedback.type">
            <template v-if="feedback.type === 'correct'">✅ 正确！</template>
            <template v-else>
              ❌ 错误，正确答案是：<strong>{{ feedback.correctAnswer }}</strong>
            </template>
          </div>

          <button v-if="feedback && feedback.type === 'correct'" class="btn-primary next-btn" @click="advance">
            下一题 →
          </button>
          <button v-if="feedback && feedback.type === 'wrong'" class="btn-primary next-btn" @click="startTypePhase">
            手动输入 3 遍 →
          </button>
        </template>

        <!-- Type phase: manual input 3 times -->
        <template v-if="phase === 'type'">
          <div class="input-area">
            <input
              ref="inputRef"
              v-model="typeInput"
              class="spell-input"
              placeholder="输入英文单词..."
              @keyup.enter="submitType"
            />
            <button class="btn-primary" @click="submitType" :disabled="!typeInput.trim()">确认</button>
          </div>

          <div v-if="typeFeedback" class="feedback" :class="typeFeedback.type">
            <template v-if="typeFeedback.type === 'correct'">
              ✅ 第 {{ typePassCount }} 遍正确！{{ typePassCount < 3 ? '还需输入 ' + (3 - typePassCount) + ' 遍' : '' }}
            </template>
            <template v-else>
              ❌ 错误，正确答案是：<strong>{{ typeFeedback.correctAnswer }}</strong>
            </template>
          </div>

          <div class="type-progress">
            <span v-for="i in 3" :key="i" class="dot" :class="{ filled: i <= typePassCount }"></span>
          </div>

          <button v-if="typePassCount >= 3" class="btn-primary next-btn" @click="advance">
            下一题 →
          </button>
        </template>
      </template>
    </template>
  </div>
</template>

<script>
import { ref, onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api/index.js'

const VOWELS = 'aeiou'
const CONSONANTS = 'bcdfghjklmnpqrstvwxyz'

function modifyLetter(ch) {
  const lower = ch.toLowerCase()
  if (VOWELS.includes(lower)) {
    const pool = VOWELS.replace(lower, '')
    return pool[Math.floor(Math.random() * pool.length)]
  }
  const pool = CONSONANTS.replace(lower, '')
  return pool[Math.floor(Math.random() * pool.length)]
}

function generateDistractors(word, count) {
  const len = word.length
  if (len <= 1) return []
  const result = new Set()
  let attempts = 0
  while (result.size < count && attempts < 100) {
    attempts++
    const numChanges = len <= 3 ? 1 : (Math.random() < 0.5 ? 1 : 2)
    const pool = []
    for (let i = 1; i < len; i++) pool.push(i)
    for (let i = pool.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [pool[i], pool[j]] = [pool[j], pool[i]]
    }
    const chars = word.split('')
    for (const pos of pool.slice(0, numChanges)) {
      chars[pos] = modifyLetter(chars[pos])
    }
    const candidate = chars.join('')
    if (candidate !== word) result.add(candidate)
  }
  return Array.from(result)
}

function shuffle(arr) {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

export default {
  name: 'Choice',
  setup() {
    const route = useRoute()
    const words = ref([])
    const current = ref(0)
    const shuffledOptions = ref([])
    const selected = ref(null)
    const feedback = ref(null)
    const optionLetters = ['A', 'B', 'C', 'D']
    const phase = ref('choice')
    const typeInput = ref('')
    const typePassCount = ref(0)
    const typeFeedback = ref(null)
    const inputRef = ref(null)

    const loadWords = async () => {
      const sectionId = parseInt(route.query.sectionId)
      const wordId = parseInt(route.query.wordId)
      if (sectionId) {
        words.value = shuffle(await api.getSectionWords(sectionId))
      } else if (wordId) {
        words.value = [await api.getWord(wordId)]
      } else {
        return
      }
      resetQuestion()
    }

    const resetQuestion = () => {
      const word = words.value[current.value]
      if (!word) return
      selected.value = null
      feedback.value = null
      phase.value = 'choice'
      typeInput.value = ''
      typePassCount.value = 0
      typeFeedback.value = null
      const distractors = generateDistractors(word.english, 3)
      const allOptions = [word.english, ...distractors]
      shuffledOptions.value = shuffle(allOptions)
    }

    const selectOption = async (opt) => {
      if (feedback.value) return
      selected.value = opt
      const word = words.value[current.value]
      if (opt === word.english) {
        feedback.value = { type: 'correct' }
        api.submitRecord(word.id, 'choice', 1)
      } else {
        feedback.value = { type: 'wrong', correctAnswer: word.english }
        await api.submitAnswer(word.id, opt)
        api.submitRecord(word.id, 'choice', 0)
      }
    }

    const startTypePhase = () => {
      phase.value = 'type'
      typeInput.value = ''
      typePassCount.value = 0
      typeFeedback.value = null
      nextTick(() => {
        if (inputRef.value) inputRef.value.focus()
      })
    }

    const submitType = () => {
      if (!typeInput.value.trim()) return
      if (typePassCount.value >= 3) return

      const word = words.value[current.value]
      const correct = typeInput.value.trim().toLowerCase() === word.english.toLowerCase()

      if (!correct) {
        typeFeedback.value = { type: 'wrong', correctAnswer: word.english }
        api.submitRecord(word.id, 'choice', 0)
        typeInput.value = ''
        return
      }

      typePassCount.value++
      api.submitRecord(word.id, 'choice', 1)
      typeFeedback.value = { type: 'correct' }
      typeInput.value = ''

      if (typePassCount.value < 3) {
        nextTick(() => {
          if (inputRef.value) inputRef.value.focus()
        })
      }
    }

    const advance = () => {
      current.value++
      nextTick(() => resetQuestion())
    }

    const optionClass = (opt) => {
      if (!feedback.value) return ''
      const word = words.value[current.value]
      if (opt === word.english) return 'is-correct'
      if (opt === selected.value && opt !== word.english) return 'is-wrong'
      return 'is-dimmed'
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
      nextTick(() => resetQuestion())
    }

    watch(() => route.query.sectionId, loadWords)
    onMounted(loadWords)

    return { words, current, shuffledOptions, selected, feedback, optionLetters, phase, typeInput, typePassCount, typeFeedback, inputRef, selectOption, startTypePhase, submitType, advance, optionClass, speak, restart }
  }
}
</script>

<style scoped>
.choice-page { max-width: 500px; margin: 0 auto; text-align: center; }
.empty { text-align: center; padding: 40px; color: #999; }
.empty a { color: #4f46e5; }
.progress-info { margin-bottom: 8px; color: #666; font-size: 14px; }
.progress-bar { height: 6px; background: #e0e7ff; border-radius: 3px; margin-top: 6px; overflow: hidden; }
.progress-fill { height: 100%; background: #ec4899; transition: width 0.3s; border-radius: 3px; }
.word-label { font-size: 13px; color: #999; margin-bottom: 12px; }
.hint-card { margin-bottom: 24px; padding: 24px; }
.chinese-word { font-size: 32px; font-weight: bold; color: #333; margin-bottom: 8px; }
.speak-btn { font-size: 15px; }
.options { display: flex; flex-direction: column; gap: 12px; margin-bottom: 20px; }
.option-btn {
  display: flex; align-items: center; gap: 12px;
  padding: 16px 20px; font-size: 20px; border: 3px solid #e0e7ff;
  border-radius: 16px; background: #fff; cursor: pointer;
  transition: all 0.2s; text-align: left;
}
.option-btn:hover:not(:disabled) { border-color: #4f46e5; background: #f0f4ff; }
.option-btn:disabled { cursor: default; }
.option-btn.is-correct { border-color: #22c55e; background: #f0fdf4; color: #22c55e; }
.option-btn.is-wrong { border-color: #ef4444; background: #fef2f2; color: #ef4444; }
.option-btn.is-dimmed { opacity: 0.5; }
.option-label {
  width: 28px; height: 28px; display: flex; align-items: center; justify-content: center;
  border-radius: 50%; background: #f3f4f6; font-size: 14px; font-weight: bold; color: #666;
  flex-shrink: 0;
}
.option-btn.is-correct .option-label { background: #22c55e; color: #fff; }
.option-btn.is-wrong .option-label { background: #ef4444; color: #fff; }
.feedback { font-size: 20px; padding: 8px; border-radius: 8px; margin-bottom: 16px; }
.feedback.correct { color: #22c55e; }
.feedback.wrong { color: #ef4444; }
.next-btn { font-size: 18px; padding: 12px 40px; margin-top: 8px; }
.input-area { display: flex; gap: 12px; margin-top: 20px; justify-content: center; }
.spell-input { flex: 1; max-width: 300px; font-size: 20px; text-align: center; padding: 12px; border-width: 3px; }
.type-progress { display: flex; gap: 10px; justify-content: center; margin: 16px 0; }
.dot {
  width: 16px; height: 16px; border-radius: 50%;
  background: #e0e7ff; transition: background 0.3s;
}
.dot.filled { background: #ec4899; }
.result-card { text-align: center; padding: 40px; margin-top: 40px; }
.result-text { font-size: 18px; color: #666; margin: 16px 0; }
.result-actions { display: flex; gap: 16px; justify-content: center; margin-top: 24px; }
</style>

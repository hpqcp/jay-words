<template>
  <div class="quiz-page">
    <div v-if="words.length === 0" class="empty">
      <p>该章节暂无单词</p>
      <router-link to="/">返回首页</router-link>
    </div>
    <template v-else-if="finished">
      <div class="card result-card">
        <h2>🎉 完成测验！</h2>
        <p class="result-text">
          共 {{ words.length }} 题，正确 {{ correctCount }} 题，
          错误 {{ words.length - correctCount }} 题
        </p>
        <p class="result-pct">正确率：{{ Math.round(correctCount / words.length * 100) }}%</p>
        <div class="result-actions">
          <button class="btn-primary" @click="restart">重新测验</button>
          <router-link to="/" class="btn-ghost" style="padding: 8px 20px; border-radius: 8px; text-decoration: none;">返回首页</router-link>
        </div>
      </div>
    </template>
    <template v-else>
      <div class="progress-info">
        <span>{{ current + 1 }} / {{ words.length }}</span>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: ((current + 1) / words.length * 100) + '%' }"></div>
        </div>
      </div>

      <div class="card quiz-card">
        <div class="quiz-prompt">
          <div class="chinese-word">{{ words[current].chinese }}</div>
          <button class="btn-ghost speak-btn" @click="speak">🔊 听发音</button>
        </div>
        <input
          ref="inputRef"
          v-model="answer"
          class="quiz-input"
          placeholder="输入英文单词..."
          @keyup.enter="submit"
        />
        <div v-if="feedback" class="feedback" :class="feedback.correct ? 'correct' : 'wrong'">
          <template v-if="feedback.correct">✅ 正确！</template>
          <template v-else>
            ❌ 错误，正确答案是：<strong>{{ feedback.correct_answer }}</strong>
          </template>
        </div>
        <button class="btn-primary submit-btn" @click="submit" :disabled="!answer.trim()">
          {{ feedback ? '下一题 →' : '确认' }}
        </button>
      </div>
    </template>
  </div>
</template>

<script>
import { ref, onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api/index.js'

export default {
  name: 'Quiz',
  setup() {
    const route = useRoute()
    const words = ref([])
    const current = ref(0)
    const answer = ref('')
    const feedback = ref(null)
    const finished = ref(false)
    const correctCount = ref(0)
    const inputRef = ref(null)

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
    }

    const submit = async () => {
      if (feedback.value) {
        nextQuestion()
        return
      }
      if (!answer.value.trim()) return
      const wordId = words.value[current.value].id
      const result = await api.submitAnswer(wordId, answer.value)
      feedback.value = result
      api.submitRecord(wordId, 'quiz', result.correct ? 1 : 0)
      if (result.correct) correctCount.value++
      nextTick(() => { if (inputRef.value) inputRef.value.focus() })
    }

    const nextQuestion = () => {
      if (current.value < words.value.length - 1) {
        current.value++
        answer.value = ''
        feedback.value = null
        nextTick(() => { if (inputRef.value) inputRef.value.focus() })
      } else {
        finished.value = true
      }
    }

    const restart = () => {
      current.value = 0
      answer.value = ''
      feedback.value = null
      finished.value = false
      correctCount.value = 0
    }

    const speak = () => {
      if (!window.speechSynthesis) return
      const word = words.value[current.value]
      const utter = new SpeechSynthesisUtterance(word.english)
      utter.lang = 'en-US'
      utter.rate = 0.9
      speechSynthesis.speak(utter)
    }

    watch(() => route.query.sectionId, loadWords)
    onMounted(() => {
      loadWords()
      nextTick(() => { if (inputRef.value) inputRef.value.focus() })
    })

    return { words, current, answer, feedback, finished, correctCount, inputRef, submit, restart, speak }
  }
}
</script>

<style scoped>
.quiz-page { max-width: 500px; margin: 0 auto; text-align: center; }
.empty { text-align: center; padding: 40px; color: #999; }
.empty a { color: #4f46e5; }
.progress-info { margin-bottom: 16px; color: #666; font-size: 14px; }
.progress-bar { height: 6px; background: #e0e7ff; border-radius: 3px; margin-top: 8px; overflow: hidden; }
.progress-fill { height: 100%; background: #22c55e; transition: width 0.3s; border-radius: 3px; }
.quiz-card { min-height: 280px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 20px; }
.chinese-word { font-size: 36px; font-weight: bold; color: #333; }
.speak-btn { font-size: 16px; margin-top: 8px; }
.quiz-input { width: 100%; font-size: 24px; text-align: center; padding: 12px; border-width: 3px; }
.feedback { font-size: 20px; padding: 8px 16px; border-radius: 8px; }
.feedback.correct { color: #22c55e; }
.feedback.wrong { color: #ef4444; }
.submit-btn { font-size: 18px; padding: 12px 40px; }
.submit-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.result-card { text-align: center; padding: 40px; }
.result-text { font-size: 18px; color: #666; margin: 16px 0; }
.result-pct { font-size: 24px; font-weight: bold; color: #4f46e5; margin: 16px 0; }
.result-actions { display: flex; gap: 16px; justify-content: center; margin-top: 24px; }
</style>

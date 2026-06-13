<template>
  <div class="flashcard-page">
    <div v-if="words.length === 0" class="empty">
      <p>该章节暂无单词</p>
      <router-link to="/">返回首页</router-link>
    </div>
    <template v-else>
      <div class="progress-info">
        <span>{{ doneCount }} / {{ words.length * 2 }} 遍</span>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: (doneCount / (words.length * 2) * 100) + '%' }"></div>
        </div>
      </div>

      <div v-if="current >= words.length" class="card result-card">
        <h2>🎉 全部完成！</h2>
        <p class="result-text">共 {{ words.length }} 词，每词 2 遍，全部掌握</p>
        <div class="result-actions">
          <button class="btn-primary" @click="restart">重新学习</button>
          <router-link to="/" class="btn-ghost" style="padding: 8px 20px; border-radius: 8px; text-decoration: none;">返回首页</router-link>
        </div>
      </div>

      <template v-else>
        <div class="word-label">
          第 {{ current + 1 }} / {{ words.length }} 词 · {{ pass === 0 ? '第1遍' : '第2遍' }}
        </div>

        <div class="card-container" @click="flip">
          <div class="flashcard" :class="{ flipped: isFlipped }">
            <div class="card-front">
              <div class="card-word">{{ words[current].english }}</div>
              <div v-if="words[current].phonetic" class="card-phonetic">{{ words[current].phonetic }}</div>
              <div class="speak-row">
                <button class="speak-btn" @click.stop="speak(0.9)" title="正常语速">🔊</button>
                <button class="speak-btn slow" @click.stop="speak(0.4)" title="慢速">🐢</button>
              </div>
              <div class="card-hint">点击翻转看中文</div>
            </div>
            <div class="card-back">
              <div class="card-word">{{ words[current].chinese }}</div>
              <div v-if="words[current].phonetic" class="card-phonetic">{{ words[current].phonetic }}</div>
              <div class="speak-row">
                <button class="speak-btn" @click.stop="speak(0.9)" title="正常语速">🔊</button>
                <button class="speak-btn slow" @click.stop="speak(0.4)" title="慢速">🐢</button>
              </div>
            </div>
          </div>
        </div>

        <div class="input-area">
          <input
            ref="inputRef"
            v-model="userInput"
            class="spell-input"
            :placeholder="isFlipped ? '输入英文单词...' : '请先点击卡片翻转'"
            :disabled="!isFlipped"
            @keyup.enter="submitInput"
          />
          <button class="btn-primary" @click="submitInput" :disabled="!isFlipped || !userInput.trim()">确认</button>
        </div>

        <div v-if="feedback" class="feedback" :class="feedback.type">
          <template v-if="feedback.type === 'correct1'">✅ 第1遍正确！再输入一遍确认</template>
          <template v-else-if="feedback.type === 'correct2'">
            🎉 掌握！<button class="btn-next" @click="advance">下一词 →</button>
          </template>
          <template v-else-if="feedback.type === 'wrong'">
            ❌ 错误，正确答案是：<strong>{{ feedback.correctAnswer }}</strong>
          </template>
        </div>
      </template>
    </template>
  </div>
</template>

<script>
import { ref, onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api/index.js'

export default {
  name: 'Flashcard',
  setup() {
    const route = useRoute()
    const words = ref([])
    const current = ref(0)
    const pass = ref(0)
    const isFlipped = ref(false)
    const userInput = ref('')
    const feedback = ref(null)
    const inputRef = ref(null)
    const doneCount = ref(0)

    const loadWords = async () => {
      const sectionId = parseInt(route.query.sectionId)
      const wordId = parseInt(route.query.wordId)
      if (sectionId) {
        words.value = await api.getSectionWords(sectionId)
      } else if (wordId) {
        words.value = [await api.getWord(wordId)]
      } else {
        return
      }
      current.value = 0
      pass.value = 0
      isFlipped.value = false
      userInput.value = ''
      feedback.value = null
      doneCount.value = 0
    }

    const flip = () => {
      if (!isFlipped.value) {
        isFlipped.value = true
        nextTick(() => {
          if (inputRef.value) inputRef.value.focus()
        })
      }
    }

    const advance = () => {
      current.value++
      pass.value = 0
      isFlipped.value = false
      feedback.value = null
      userInput.value = ''
    }

    const submitInput = async () => {
      if (!isFlipped.value || !userInput.value.trim()) return
      if (feedback.value && feedback.value.type === 'correct2') return

      const word = words.value[current.value]
      const correct = userInput.value.trim().toLowerCase() === word.english.toLowerCase()

      if (!correct) {
        feedback.value = { type: 'wrong', correctAnswer: word.english }
        await api.submitAnswer(word.id, userInput.value)
        api.submitRecord(word.id, 'flashcard', 0)
        return
      }

      if (pass.value === 0) {
        pass.value = 1
        doneCount.value++
        feedback.value = { type: 'correct1' }
        userInput.value = ''
        api.submitRecord(word.id, 'flashcard', 1)
        nextTick(() => { if (inputRef.value) inputRef.value.focus() })
      } else {
        doneCount.value++
        feedback.value = { type: 'correct2' }
        userInput.value = ''
        api.submitRecord(word.id, 'flashcard', 1)
      }
    }

    const speak = (rate = 0.9) => {
      if (!window.speechSynthesis) return
      const word = words.value[current.value]
      if (!word) return
      window.speechSynthesis.cancel()
      const utter = new SpeechSynthesisUtterance(word.english)
      utter.lang = 'en-US'
      utter.rate = rate
      speechSynthesis.speak(utter)
    }

    const restart = () => {
      current.value = 0
      pass.value = 0
      isFlipped.value = false
      userInput.value = ''
      feedback.value = null
      doneCount.value = 0
    }

    const handleKeydown = (e) => {
      if (e.key === ' ' && !isFlipped.value) {
        e.preventDefault()
        flip()
      }
    }

    watch(() => route.query.sectionId, loadWords)
    onMounted(() => {
      loadWords()
      window.addEventListener('keydown', handleKeydown)
    })

    return { words, current, pass, isFlipped, userInput, feedback, inputRef, doneCount, flip, advance, submitInput, speak, restart }
  }
}
</script>

<style scoped>
.flashcard-page { max-width: 500px; margin: 0 auto; text-align: center; }
.empty { text-align: center; padding: 40px; color: #999; }
.empty a { color: #4f46e5; }
.progress-info { margin-bottom: 8px; color: #666; font-size: 14px; }
.progress-bar { height: 6px; background: #e0e7ff; border-radius: 3px; margin-top: 6px; overflow: hidden; }
.progress-fill { height: 100%; background: #4f46e5; transition: width 0.3s; border-radius: 3px; }
.word-label { font-size: 13px; color: #999; margin-bottom: 8px; }
.card-container { perspective: 1000px; cursor: pointer; min-height: 220px; margin: 12px 0; }
.flashcard { width: 100%; min-height: 210px; position: relative; transition: transform 0.5s; transform-style: preserve-3d; }
.flashcard.flipped { transform: rotateY(180deg); }
.card-front, .card-back {
  position: absolute; top: 0; left: 0; width: 100%; min-height: 210px;
  backface-visibility: hidden; display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  background: #fff; border-radius: 20px;
  box-shadow: 0 4px 20px rgba(79,70,229,0.12); padding: 28px;
}
.card-back { transform: rotateY(180deg); background: linear-gradient(135deg, #eef2ff, #fff); }
.card-word { font-size: 32px; font-weight: bold; color: #333; }
.card-phonetic { font-size: 16px; color: #999; margin-top: 6px; }
.speak-row { display: flex; gap: 8px; margin-top: 12px; }
.speak-btn {
  margin-top: 12px; background: #e0e7ff; border: none; font-size: 24px;
  width: 48px; height: 48px; border-radius: 50%; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: background 0.2s;
}
.speak-btn:hover { background: #c7d2fe; }
.speak-btn.slow { font-size: 20px; background: #fef3c7; }
.speak-btn.slow:hover { background: #fde68a; }
.card-hint { font-size: 13px; color: #ccc; margin-top: 16px; }
.input-area { display: flex; gap: 12px; margin-top: 16px; justify-content: center; }
.spell-input { flex: 1; max-width: 300px; font-size: 20px; text-align: center; padding: 12px; border-width: 3px; }
.spell-input:disabled { background: #f5f5f5; border-color: #eee; }
.feedback { font-size: 18px; margin-top: 12px; padding: 8px; border-radius: 8px; }
.feedback.correct1 { color: #22c55e; }
.feedback.correct2 { color: #4f46e5; }
.feedback.wrong { color: #ef4444; }
.btn-next {
  background: #4f46e5; color: #fff; border: none; padding: 6px 18px;
  border-radius: 6px; font-size: 16px; cursor: pointer; margin-left: 10px;
}
.btn-next:hover { opacity: 0.85; }
.result-card { text-align: center; padding: 40px; margin-top: 40px; }
.result-text { font-size: 18px; color: #666; margin: 16px 0; }
.result-actions { display: flex; gap: 16px; justify-content: center; margin-top: 24px; }
</style>
